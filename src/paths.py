import hashlib
from pathlib import Path
from config.config import REPORTS_DIR,PROCESSED_DIR,EMBEDDINGS_DIR,MODELS_DIR

def get_paths(filename:str,file_bytes:bytes) ->dict:
    file_hash=hashlib.sha256(file_bytes).hexdigest()[:12]
    stem=f"{Path(filename).stem}_{file_hash}"
    return {
        "pdf":REPORTS_DIR/f"{stem}.pdf",
        "txt":        PROCESSED_DIR  / f"{stem}.txt",
        "chunks":     PROCESSED_DIR  / f"{stem}_chunks.json",
        "embeddings": EMBEDDINGS_DIR / f"{stem}_embeddings.npy",
        "index":      MODELS_DIR     / f"{stem}.index",
    }