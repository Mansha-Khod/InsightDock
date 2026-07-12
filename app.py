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

def get_paths(pdf_filename: str) -> dict:
    stem = Path(pdf_filename).stem
    return {
        "pdf":        REPORTS_DIR    / pdf_filename,
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


def faiss_distance_to_similarity(distance: float) -> int:
    """Convert a FAISS L2 distance to an approximate similarity percentage."""
    similarity = max(0.0, 1.0 - distance)
    return int(round(similarity * 100))


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


# ════════════════════════════════════════════════════════════════════════════
# PROCESSING PIPELINE
# ════════════════════════════════════════════════════════════════════════════

def process_document(paths: dict) -> None:
    """
    Run the five-step pipeline, updating a progress bar and a step log.
    Records per-step timing and total elapsed time in session state.
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

        st.session_state["processed"]       = True
        st.session_state["paths"]           = paths
        st.session_state["summary"]         = None
        st.session_state["key_points"]      = None
        st.session_state["question_history"] = st.session_state.get("question_history", [])
        st.session_state["processing_time"] = f"{total_elapsed:.2f}"
        st.session_state["doc_stats"]       = compute_doc_stats(paths)

    except Exception as exc:
        progress_bar.empty()
        st.error(f"Pipeline failed: {exc}")
        st.session_state["processed"] = False


# ════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════════════

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

    if st.session_state.get("processed"):
        st.success("Document is ready.")
    elif uploaded_file:
        st.info("Click Process Document to continue.")

    # Show quick stats in sidebar once processed
    if st.session_state.get("processed") and st.session_state.get("doc_stats"):
        st.divider()
        st.markdown("**Quick Stats**")
        s = st.session_state["doc_stats"]
        st.markdown(f"Pages: **{s['pages']}**")
        st.markdown(f"Words: **{s['words']}**")
        st.markdown(f"Chunks: **{s['chunks']}**")
        st.markdown(f"Processing time: **{st.session_state.get('processing_time', '—')}s**")

    # Question history in sidebar
    history = st.session_state.get("question_history", [])
    if history:
        st.divider()
        st.markdown("**Question History**")
        for q in reversed(history[-10:]):          # show latest 10, newest first
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
    paths = get_paths(uploaded_file.name)

    with open(paths["pdf"], "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Reset state for new document
    for key in ("processed", "paths", "summary", "key_points",
                "doc_stats", "processing_time"):
        st.session_state[key] = None
    st.session_state["question_history"] = []

    if (
        paths["index"].exists()
        and paths["chunks"].exists()
        and paths["embeddings"].exists()
        and paths["txt"].exists()
    ):
        st.success(f"{uploaded_file.name} was already processed. Loading from cache.")
        st.session_state["processed"]       = True
        st.session_state["paths"]           = paths
        st.session_state["doc_stats"]       = compute_doc_stats(paths)
        st.session_state["processing_time"] = "cached"
    else:
        process_document(paths)
        if st.session_state.get("processed"):
            st.success(f"{uploaded_file.name} processed successfully.")


# ════════════════════════════════════════════════════════════════════════════
# POST-PROCESSING UI
# ════════════════════════════════════════════════════════════════════════════

if st.session_state.get("processed") and st.session_state.get("paths"):
    paths = st.session_state["paths"]
    stats = st.session_state.get("doc_stats", {})
    proc_time = st.session_state.get("processing_time", "—")

    # ── Document Statistics card ─────────────────────────────────────────────
    with st.container(border=True):
        st.markdown("**Document Statistics**")

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
                                    dist       = src.get("distance", 1.0)
                                    similarity = faiss_distance_to_similarity(dist)
                                    conf       = confidence_label(dist)
                                    label      = (
                                        f"Source {i} — "
                                        f"{conf}  |  "
                                        f"Pages: {src.get('pages', '—')}"
                                    )
                                    with st.expander(label, expanded=(i == 1)):
                                        s1, s2 = st.columns(2)
                                        s1.metric("Confidence", conf)
                                        s2.metric("Pages",      src.get("pages", "—"))
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

                    st.session_state["summary"] = summary
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

        if st.session_state.get("summary"):
            st.markdown("### Summary")
            st.markdown(st.session_state["summary"])
            st.download_button(
                label="Download Executive Summary",
                data=st.session_state["summary"],
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
                    st.session_state["key_points"] = key_points
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

        if st.session_state.get("key_points"):
            st.markdown("### Key Insights")
            raw = st.session_state["key_points"]

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
