import faiss
import numpy as np
import json
from src.model_loader import sentence_transformer_model
from config.config import EMBEDDINGS_DIR
from config.config import MODELS_DIR
from config.config import PROCESSED_DIR

def build_index(embeddings_path,index_path):

    embeddings = np.load(
        EMBEDDINGS_DIR/embeddings_path
    )

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(dimension)

    index.add(embeddings)

    faiss.write_index(
    index,
    str(MODELS_DIR / index_path)  
)

    print("Index created successfully!")
    print(f"Total vectors: {index.ntotal}")


def search(query,index_path,chunk_json_path,k=3):

    
    index = faiss.read_index(
    str(MODELS_DIR / index_path)
)

    
    query_embedding = sentence_transformer_model.encode(
        query,
        convert_to_numpy=True
    ).reshape(1, -1)

    distances, indices = index.search(query_embedding, k)

    with open(
        PROCESSED_DIR/chunk_json_path,
        "r",
        encoding="utf-8"
    ) as f:

        chunks = json.load(f)

    results=[]

    for rank, chunk_index in enumerate(indices[0], start=1):

        chunk = chunks[chunk_index]
        results.append({
            "chunk": chunk,
            "distance": float(distances[0][rank-1])
        })
    return results

def load_all_chunks(chunk_json_path):
    with open(PROCESSED_DIR/chunk_json_path,"r",encoding="utf-8") as f:
        chunks=json.load(f)
        return chunks

