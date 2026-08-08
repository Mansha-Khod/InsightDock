import json
import numpy as np

def compute_doc_stats(paths: dict) -> dict:
    stats = {
        "pages": "—", "words": "—", "chunks": "—",
        "avg_chunk_words": "—", "largest_chunk": "—",
        "smallest_chunk": "—", "embedding_dim": "—",
    }

    try:
        text = paths["txt"].read_text(encoding="utf-8", errors="ignore")
        stats["words"] = len(text.split())
        stats["pages"] = max(1, text.count("== PAGE"))
    except Exception:
        pass

    try:
        with open(paths["chunks"], "r", encoding="utf-8") as f:
            chunks = json.load(f)
        word_counts = [len(c["text"].split()) for c in chunks]
        stats["chunks"] = len(chunks)
        stats["avg_chunk_words"] = int(np.mean(word_counts))
        stats["largest_chunk"] = max(word_counts)
        stats["smallest_chunk"] = min(word_counts)
    except Exception:
        pass

    try:
        emb = np.load(paths["embeddings"])
        stats["embedding_dim"] = emb.shape[1] if emb.ndim == 2 else "—"
    except Exception:
        pass

    return stats