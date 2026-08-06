import json
import time
import numpy as np
import streamlit as st
from pathlib import Path
from datetime import datetime

# ── Backend imports ──────────────────────────────────────────────────────────
from src.pdf_loader        import extract_text
from src.chunker           import text_to_chunks
from src.embeddings        import generate_embeddings
from src.vector_store      import build_index
from src.rag               import ask_gemini
from src.executive_summary import generate_executive_summary
from src.key_points        import generate_key_points

# ── Directory paths ──────────────────────────────────────────────────────────
REPORTS_DIR    = Path("data/reports")
PROCESSED_DIR  = Path("data/processed")
EMBEDDINGS_DIR = Path("data/embeddings")
MODELS_DIR     = Path("models")

for _dir in (REPORTS_DIR, PROCESSED_DIR, EMBEDDINGS_DIR, MODELS_DIR):
    _dir.mkdir(parents=True, exist_ok=True)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Intelligent Document Assistant",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ════════════════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════════════════

import hashlib

def get_paths(uploaded_file) -> dict:
    file_hash = hashlib.sha256(uploaded_file.getbuffer()).hexdigest()[:12]
    stem = f"{Path(uploaded_file.name).stem}_{file_hash}"
    return {
        "pdf":        REPORTS_DIR    / f"{stem}.pdf",
        "txt":        PROCESSED_DIR  / f"{stem}.txt",
        "chunks":     PROCESSED_DIR  / f"{stem}_chunks.json",
        "embeddings": EMBEDDINGS_DIR / f"{stem}_embeddings.npy",
        "index":      MODELS_DIR     / f"{stem}.index",
    }


def compute_doc_stats(paths: dict) -> dict:
    """Compute document and chunk statistics from processed files."""
    stats = {
        "pages": "—", "words": "—", "chunks": "—",
        "avg_chunk_words": "—", "largest_chunk": "—",
        "smallest_chunk": "—", "embedding_dim": "—",
    }

    # Word count from extracted text
    try:
        text = paths["txt"].read_text(encoding="utf-8", errors="ignore")
        words = text.split()
        stats["words"] = f"{len(words):,}"
    except Exception:
        pass

    try:
        page_markers = text.count("== PAGE")
        stats["pages"] = max(1, page_markers)
    except Exception:
        pass

    # Chunk-level stats
    try:
        with open(paths["chunks"], "r", encoding="utf-8") as f:
            chunks = json.load(f)
        chunk_word_counts = [len(chunk["text"].split()) for chunk in chunks]
        stats["chunks"] = len(chunks)
        stats["avg_chunk_words"] = f"{int(np.mean(chunk_word_counts)):,}"
        stats["largest_chunk"] = f"{max(chunk_word_counts):,}"
        stats["smallest_chunk"] = f"{min(chunk_word_counts):,}"
    except Exception:
        pass

    # Embedding dimension
    try:
        emb = np.load(paths["embeddings"])
        stats["embedding_dim"] = emb.shape[1] if emb.ndim == 2 else "—"
    except Exception:
        pass

    return stats


def confidence_label(distance: float) -> str:
    """Return a human-readable confidence label based on FAISS distance."""
    if distance <= 0.4:
        return "High confidence"
    elif distance <= 0.8:
        return "Medium confidence"
    else:
        return "Low confidence"


def format_pipeline_log(log: list[dict]) -> None:
    """Render the step-by-step pipeline log with status icons."""
    st.markdown("**Pipeline Steps**")
    for step in log:
        icon   = "✓" if step["status"] == "done" else ("✗" if step["status"] == "error" else "...")
        timing = f"  ({step['elapsed']:.2f}s)" if step.get("elapsed") else ""
        st.markdown(f"{icon} &nbsp; {step['label']}{timing}")


def ensure_documents_store() -> None:
    """Make sure the multi-document session state containers exist."""
    if "documents" not in st.session_state:
        st.session_state["documents"] = {}   # stem -> {paths, display_name, summary, key_points, doc_stats, processing_time}
    if "question_history" not in st.session_state:
        st.session_state["question_history"] = []


# ════════════════════════════════════════════════════════════════════════════
# PROCESSING PIPELINE
# ════════════════════════════════════════════════════════════════════════════

def process_document(paths: dict, display_name: str) -> None:
    """
    Run the five-step pipeline, updating a progress bar and a step log.
    On success, registers the document under its own entry in
    st.session_state["documents"], keyed by its hash stem, so multiple
    documents can be processed and kept around in the same session.
    """
    pipeline_log   = []
    total_start    = time.perf_counter()
    progress_bar   = st.progress(0, text="Starting pipeline...")
    log_placeholder = st.empty()

    def run_step(label: str, fn, progress_pct: int):
        """Execute one pipeline step; update log and progress bar."""
        pipeline_log.append({"label": label, "status": "running", "elapsed": None})
        log_placeholder.empty()
        with log_placeholder.container():
            format_pipeline_log(pipeline_log)

        step_start = time.perf_counter()
        try:
            fn()
            elapsed = time.perf_counter() - step_start
            pipeline_log[-1]["status"]  = "done"
            pipeline_log[-1]["elapsed"] = elapsed
            progress_bar.progress(progress_pct, text=f"{label} complete.")
        except Exception as exc:
            pipeline_log[-1]["status"] = "error"
            log_placeholder.empty()
            with log_placeholder.container():
                format_pipeline_log(pipeline_log)
            raise exc
        finally:
            log_placeholder.empty()
            with log_placeholder.container():
                format_pipeline_log(pipeline_log)

    try:
        run_step(
            "Extract text from PDF", progress_pct=20,
            fn=lambda: extract_text(str(paths["pdf"]), str(paths["txt"])),
        )
        run_step(
            "Chunk document", progress_pct=40,
            fn=lambda: text_to_chunks(paths["txt"].name, paths["chunks"].name),
        )
        run_step(
            "Generate embeddings", progress_pct=65,
            fn=lambda: generate_embeddings(paths["chunks"].name, paths["embeddings"].name),
        )
        run_step(
            "Build FAISS index", progress_pct=90,
            fn=lambda: build_index(paths["embeddings"].name, paths["index"].name),
        )

        total_elapsed = time.perf_counter() - total_start
        pipeline_log.append({"label": "Ready", "status": "done", "elapsed": None})
        progress_bar.progress(100, text="Processing complete.")

        log_placeholder.empty()
        with log_placeholder.container():
            format_pipeline_log(pipeline_log)

        ensure_documents_store()
        stem = paths["pdf"].stem
        st.session_state["documents"][stem] = {
            "paths": paths,
            "display_name": display_name,
            "summary": None,
            "key_points": None,
            "doc_stats": compute_doc_stats(paths),
            "processing_time": f"{total_elapsed:.2f}",
        }
        st.session_state["active_stem"] = stem

    except Exception as exc:
        progress_bar.empty()
        st.error(f"Pipeline failed: {exc}")
        # Failed docs simply never get added to st.session_state["documents"] —
        # there's no single "processed" flag to fall back to anymore now that
        # multiple documents can exist at once.


# ════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════════════

ensure_documents_store()

with st.sidebar:
    st.title("Document Upload")
    st.markdown("Upload a PDF and click **Process Document** to begin.")

    uploaded_file = st.file_uploader(
        label="Choose a PDF file",
        type=["pdf"],
        help="Only PDF files are supported.",
    )

    process_btn = st.button(
        "Process Document",
        use_container_width=True,
        disabled=(uploaded_file is None),
        type="primary",
    )

    documents = st.session_state["documents"]

    if documents:
        st.success(f"{len(documents)} document(s) ready.")
    elif uploaded_file:
        st.info("Click Process Document to continue.")

    # Document switcher — which processed document the main panel shows.
    # (This is separate from the multi-select used for cross-document search,
    # added in step 1.2 — this just controls what stats/summary are displayed.)
    active_stem = st.session_state.get("active_stem")
    if documents:
        st.divider()
        stem_to_name = {stem: info["display_name"] for stem, info in documents.items()}
        stem_options = list(stem_to_name.keys())
        default_index = stem_options.index(active_stem) if active_stem in stem_options else len(stem_options) - 1

        chosen_stem = st.selectbox(
            "Active document",
            options=stem_options,
            format_func=lambda s: stem_to_name[s],
            index=default_index,
        )
        st.session_state["active_stem"] = chosen_stem
        active_stem = chosen_stem

    # Show quick stats in sidebar for the active document
    if active_stem and active_stem in documents:
        active_doc = documents[active_stem]
        s = active_doc.get("doc_stats", {})
        if s:
            st.divider()
            st.markdown("**Quick Stats**")
            st.markdown(f"Pages: **{s.get('pages', '—')}**")
            st.markdown(f"Words: **{s.get('words', '—')}**")
            st.markdown(f"Chunks: **{s.get('chunks', '—')}**")
            st.markdown(f"Processing time: **{active_doc.get('processing_time', '—')}s**")

    # Question history in sidebar
    history = st.session_state.get("question_history", [])
    if history:
        st.divider()
        st.markdown("**Question History**")
        for q in reversed(history[-10:]):          
            st.markdown(f"- {q}")

    st.divider()
    st.caption("Intelligent Document Assistant")


# ════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ════════════════════════════════════════════════════════════════════════════

st.title("Intelligent Document Assistant")
st.markdown(
    "Upload any PDF, process it through the RAG pipeline, then ask questions, "
    "generate an executive summary, or extract key insights."
)
st.divider()


# ── Process button handler ───────────────────────────────────────────────────
if process_btn and uploaded_file is not None:
    paths = get_paths(uploaded_file)
    stem = paths["pdf"].stem

    with open(paths["pdf"], "wb") as f:
        f.write(uploaded_file.getbuffer())

    ensure_documents_store()

    if (
        paths["index"].exists()
        and paths["chunks"].exists()
        and paths["embeddings"].exists()
        and paths["txt"].exists()
    ):
        st.success(f"{uploaded_file.name} was already processed. Loading from cache.")
        st.session_state["documents"][stem] = {
            "paths": paths,
            "display_name": uploaded_file.name,
            "summary": None,
            "key_points": None,
            "doc_stats": compute_doc_stats(paths),
            "processing_time": "cached",
        }
        st.session_state["active_stem"] = stem
    else:
        process_document(paths, uploaded_file.name)
        if stem in st.session_state.get("documents", {}):
            st.success(f"{uploaded_file.name} processed successfully.")


# ════════════════════════════════════════════════════════════════════════════
# POST-PROCESSING UI
# ════════════════════════════════════════════════════════════════════════════

active_stem = st.session_state.get("active_stem")
documents = st.session_state.get("documents", {})

if active_stem and active_stem in documents:
    active_doc = documents[active_stem]
    paths = active_doc["paths"]
    stats = active_doc.get("doc_stats", {})
    proc_time = active_doc.get("processing_time", "—")

    # ── Document Statistics card ─────────────────────────────────────────────
    with st.container(border=True):
        st.markdown(f"**Document Statistics** — {active_doc['display_name']}")

        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric("Pages",          stats.get("pages", "—"))
        col2.metric("Words",          stats.get("words", "—"))
        col3.metric("Chunks",         stats.get("chunks", "—"))
        col4.metric("Avg Chunk Size", f"{stats.get('avg_chunk_words', '—')} words")
        col5.metric("Embedding Dim",  stats.get("embedding_dim", "—"))
        col6.metric(
            "Processing Time",
            f"{proc_time}s" if proc_time not in ("—", "cached") else proc_time,
        )

    # ── Chunk Statistics card ────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown("**Chunk Statistics**")
        c1, c2, c3 = st.columns(3)
        c1.metric("Largest Chunk",  f"{stats.get('largest_chunk', '—')} words")
        c2.metric("Smallest Chunk", f"{stats.get('smallest_chunk', '—')} words")
        c3.metric("Average Chunk",  f"{stats.get('avg_chunk_words', '—')} words")

    st.divider()

    # ── Tabs ─────────────────────────────────────────────────────────────────
    tab_qa, tab_summary, tab_keypoints = st.tabs(
        ["💬 Ask Questions", "📋 Executive Summary", "⭐ Key Insights"]
    )

    # ── TAB 1: Ask Questions ─────────────────────────────────────────────────
    with tab_qa:
        st.subheader("Ask a Question About the Document")
        search_mode = st.radio(
            "Search mode",
            ["Hybrid (semantic + keyword)", "Semantic only"],
            horizontal=True,
        )
        mode = "hybrid" if "Hybrid" in search_mode else "semantic"

        question = st.text_input(
            label="Your question",
            placeholder="e.g. What are the key financial risks mentioned?",
            label_visibility="collapsed",
        )

        ask_btn = st.button("Ask", type="primary", key="ask_btn")

        if ask_btn:
            if not question.strip():
                st.warning("Please enter a question before clicking Ask.")
            else:
                # Save to history
                history = st.session_state.get("question_history", [])
                history.append(question)
                st.session_state["question_history"] = history

                with st.spinner("Searching the document and generating an answer..."):
                    try:
                        result = ask_gemini(
                            query=question,
                            index_path=paths["index"].name,
                            chunk_json_path=paths["chunks"].name,
                        )

                        # Support plain string or (answer, sources) tuple
                        if isinstance(result, tuple):
                            answer, sources = result[0], result[1]
                        else:
                            answer, sources = result, None

                        st.markdown("### Answer")
                        st.markdown(answer)

                        # Determine overall confidence from best source
                        if sources and isinstance(sources[0], dict):
                            best_dist = sources[0].get("distance", 1.0)
                            conf      = confidence_label(best_dist)
                            badge_col = (
                                "green"  if "High"   in conf else
                                "orange" if "Medium" in conf else "red"
                            )
                            st.markdown(
                                f"**Answer Confidence:** "
                                f":{badge_col}[{conf}]"
                            )

                        # Download answer
                        st.download_button(
                            label="Download Answer",
                            data=f"Question: {question}\n\nAnswer:\n{answer}",
                            file_name=f"answer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain",
                            key=f"dl_answer_{len(history)}",
                        )

                        # Retrieved sources
                        if sources:
                            st.markdown("### Retrieved Sources")
                            for i, src in enumerate(sources, 1):
                                if isinstance(src, dict):
                                    label      = label = f"Source {i} — Pages: {src.get('pages', '—')}"
                                    
                                    with st.expander(label, expanded=(i == 1)):
                                        st.metric("Pages", src.get("pages", "—"))
                                        if src.get("preview"):
                                            st.markdown(f"> {src['preview']}")
                                else:
                                    with st.expander(f"Source {i}", expanded=(i == 1)):
                                        st.markdown(str(src))

                    except Exception as exc:
                        error = str(exc)

                        if "RESOURCE_EXHAUSTED" in error:
                            st.warning(
                                """
                                Gemini API quota exceeded.

                                The free Gemini tier has reached its request limit.

                                Please wait a minute and try again, or use another API key.
                                """
                            )
                        else:
                            st.error(f"Could not generate an answer: {exc}")

    # ── TAB 2: Executive Summary ──────────────────────────────────────────────
    with tab_summary:
        st.subheader("Executive Summary")
        st.markdown("Generate a concise executive summary of the entire document.")

        summarize_btn = st.button(
            "Generate Summary", type="primary", key="summarize_btn"
        )

        if summarize_btn:
            with st.spinner("Generating executive summary..."):
                try:
                    summary = generate_executive_summary(
                        txt_path=paths["txt"].name
                    )

                    st.session_state["documents"][active_stem]["summary"] = summary
                except Exception as exc:
                    error = str(exc)

                    if "RESOURCE_EXHAUSTED" in error:
                        st.warning(
                            """
                            Gemini API quota exceeded.

                            The free Gemini tier has reached its request limit.

                            Please wait a minute and try again, or use another API key.
                            """
                        )
                    else:
                        st.error(f"Could not generate summary: {exc}")

        current_summary = st.session_state["documents"][active_stem].get("summary")
        if current_summary:
            st.markdown("### Summary")
            st.markdown(current_summary)
            st.download_button(
                label="Download Executive Summary",
                data=current_summary,
                file_name=f"executive_summary_{paths['pdf'].stem}.txt",
                mime="text/plain",
                key="dl_summary",
            )

    # ── TAB 3: Key Insights ───────────────────────────────────────────────────
    with tab_keypoints:
        st.subheader("Key Insights")
        st.markdown("Extract the most important points from the document.")

        keypoints_btn = st.button(
            "Generate Key Insights", type="primary", key="keypoints_btn"
        )

        if keypoints_btn:
            with st.spinner("Extracting key insights..."):
                try:
                    key_points = generate_key_points(
                        txt_path=paths["txt"].name
                    )
                    st.session_state["documents"][active_stem]["key_points"] = key_points
                except Exception as exc:
                    error = str(exc)

                    if "RESOURCE_EXHAUSTED" in error:
                        st.warning(
                            """
                            Gemini API quota exceeded.

                            The free Gemini tier has a very small daily request limit.

                            Please wait a minute and try again, or use another API key.
                            """
                        )
                    else:
                        st.error(f"Could not extract key insights: {exc}")

        current_key_points = st.session_state["documents"][active_stem].get("key_points")
        if current_key_points:
            st.markdown("### Key Insights")
            raw = current_key_points

            rendered_lines = []
            if isinstance(raw, list):
                for point in raw:
                    st.markdown(f"- {point}")
                    rendered_lines.append(f"- {point}")
            else:
                lines = [ln.strip() for ln in str(raw).splitlines() if ln.strip()]
                for line in lines:
                    prefix = "" if line.startswith(("-", "*")) else "- "
                    st.markdown(f"{prefix}{line}")
                    rendered_lines.append(f"{prefix}{line}")

            download_text = "\n".join(rendered_lines)
            st.download_button(
                label="Download Key Insights",
                data=download_text,
                file_name=f"key_insights_{paths['pdf'].stem}.txt",
                mime="text/plain",
                key="dl_keypoints",
            )

else:
    st.info(
        "Upload a PDF in the sidebar and click Process Document to get started."
    )