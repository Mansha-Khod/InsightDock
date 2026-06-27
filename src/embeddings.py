import json
import numpy as np
from src.model_loader import sentence_transformer_model

def generate_embeddings(input_json, output_npy):
    with open(input_json,"r",encoding="utf-8") as f:
        texts=[]
        chunks=json.load(f)
        for chunk in chunks:
            texts.append(chunk['text'])
        model=sentence_transformer_model
        embeddings=model.encode(texts,convert_to_numpy=True)
        
        print(type(embeddings))
        print(embeddings.shape)
    np.save(output_npy,embeddings)
    print("Embeddings saved successfully!")
    print(f"Shape: {embeddings.shape}")
generate_embeddings("C:/Users/hp/Desktop/Projects/financial-report-analyzer/data/processed/apple_2024_chunks.json","C:/Users/hp/Desktop/Projects/financial-report-analyzer/data/embeddings/apple_2024_embeddings.npy")