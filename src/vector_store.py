import faiss
import numpy as np
import json
from src.model_loader import sentence_transformer_model


def build_index():

    embeddings = np.load(
        "C:/Users/hp/Desktop/Projects/financial-report-analyzer/data/embeddings/apple_2024_embeddings.npy"
    )

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(dimension)

    index.add(embeddings)

    faiss.write_index(
        index,
        "C:/Users/hp/Desktop/Projects/financial-report-analyzer/models/apple_2024.index"
    )

    print("Index created successfully!")
    print(f"Total vectors: {index.ntotal}")


def search(query, k):

    
    index = faiss.read_index(
        "C:/Users/hp/Desktop/Projects/financial-report-analyzer/models/apple_2024.index"
    )

    
    query_embedding = sentence_transformer_model.encode(
        query,
        convert_to_numpy=True
    ).reshape(1, -1)

    distances, indices = index.search(query_embedding, k)

    with open(
        "C:/Users/hp/Desktop/Projects/financial-report-analyzer/data/processed/apple_2024_chunks.json",
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



