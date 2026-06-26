import faiss 
import numpy as np 

embeddings=np.load("C:/Users/hp/Desktop/Projects/financial-report-analyzer/data/embeddings/apple_2024_embeddings.npy")
print(embeddings.shape)

dimension=embeddings.shape[1]
index=faiss.IndexFlatL2(dimension)
index.add(embeddings)
print(index.ntotal)

faiss.write_index(
    index,
    "C:/Users/hp/Desktop/Projects/financial-report-analyzer/models/apple_2024.index"
)