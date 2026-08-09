import faiss
import numpy as np
import json
from src.model_loader import get_model
from rank_bm25 import BM25Okapi
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

    
    query_embedding = get_model.encode(
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
    k = min(k, len(chunks))
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


def search_multi(query, docs, k=3):
    all_results = []

    for doc in docs:
        index_path = doc["paths"]["index"].name
        chunk_json_path = doc["paths"]["chunks"].name
        doc_results = search(query, index_path, chunk_json_path, k=k)
        for r in doc_results:
            r["source_filename"] = doc["display_name"]
        all_results.extend(doc_results)

    all_results.sort(key=lambda r: r["distance"])
    return all_results[:k]

def bm25_search(query,chunk_json_path,k=3):
    chunks=load_all_chunks(chunk_json_path)
    tokenized_corpus=[c['text'].lower().split() for c in chunks]
    bm25=BM25Okapi(tokenized_corpus)

    tokenized_query=query.lower().split()
    scores=bm25.get_scores(tokenized_query)
    ranked_indices=np.argsort(scores)[::-1][:k]

    return [
        {"chunk": chunks[i], "bm25_score": float(scores[i])}
        for i in ranked_indices
    ]

def bm25_search_multi(query, docs, k=3):
    all_results = []
    for doc in docs:
        chunk_json_path = doc["paths"]["chunks"].name
        doc_results = bm25_search(query, chunk_json_path, k=k)
        for r in doc_results:
            r["source_filename"] = doc["display_name"]
        all_results.extend(doc_results)

    all_results.sort(key=lambda r: r["bm25_score"], reverse=True)
    return all_results[:k]