# etl/embeddings.py
from sentence_transformers import SentenceTransformer
import os
import torch

MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'
MODEL_PATH = os.getenv("MODEL_PATH", "./models/all-MiniLM-L6-v2") # Local path to store the model

# Check for GPU
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Using device: {device}")

# This will download the model if it's not already in MODEL_PATH
def load_embedding_model():
    """
    Loads the SentenceTransformer model. Downloads if not available locally.
    """
    # Check if model exists locally
    if not os.path.exists(MODEL_PATH):
        print(f"Model not found at {MODEL_PATH}. Downloading...")
        model = SentenceTransformer(MODEL_NAME)
        model.save_pretrained(MODEL_PATH)
        print(f"Model downloaded and saved to {MODEL_PATH}")
    else:
        print(f"Loading model from local path: {MODEL_PATH}")
        model = SentenceTransformer(MODEL_PATH)
    
    model.to(device) # Move model to GPU if available
    return model

def generate_embedding(model, text):
    """
    Generates a sentence embedding for the given text.
    """
    if not text:
        return None
    # Encode text to embeddings
    embeddings = model.encode(text, convert_to_tensor=True, device=device)
    return embeddings.tolist() # Convert tensor to list for storage

if __name__ == '__main__':
    # Example usage:
    model = load_embedding_model()
    
    test_text = "This is a sample piece of legislation text for testing embeddings."
    embedding = generate_embedding(model, test_text)

    if embedding:
        print(f"Generated embedding (first 5 elements): {embedding[:5]}...")
        print(f"Embedding dimension: {len(embedding)}")
    else:
        print("Failed to generate embedding.")

    test_text_2 = "Another sentence to compare semantic similarity."
    embedding_2 = generate_embedding(model, test_text_2)

    # You can later calculate cosine similarity between these.