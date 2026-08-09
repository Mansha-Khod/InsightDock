import json
import numpy as np
from src.model_loader import get_model
from config.config import EMBEDDINGS_DIR
from config.config import PROCESSED_DIR

def generate_embeddings(input_json, output_npy):
    with open(PROCESSED_DIR / input_json, "r", encoding="utf-8") as f:
        texts=[]
        chunks=json.load(f)
        texts = [chunk["text"] for chunk in chunks]
        model=get_model()
        embeddings=model.encode(texts,convert_to_numpy=True)
        
        print(type(embeddings))
        print(embeddings.shape)
    np.save(EMBEDDINGS_DIR / output_npy, embeddings)
    print("Embeddings saved successfully!")
    print(f"Shape: {embeddings.shape}")
