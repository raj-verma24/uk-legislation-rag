# etl/vector_db.py
import chromadb
import os

# Directory to store ChromaDB data
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./db/vector")

def get_chroma_client():
    """Returns a ChromaDB client (persistent client)."""
    os.makedirs(CHROMA_DB_PATH, exist_ok=True)
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    print(f"ChromaDB client initialized at: {CHROMA_DB_PATH}")
    return client

def get_legislation_collection(client):
    """
    Gets or creates the ChromaDB collection for legislation embeddings.
    """
    collection_name = "uk_legislation_embeddings"
    # Get or create collection
    collection = client.get_or_create_collection(name=collection_name)
    print(f"ChromaDB collection '{collection_name}' initialized.")
    return collection

def add_embedding_to_vectordb(collection, legislation_id, text_content, embedding):
    """
    Adds a document and its embedding to the ChromaDB collection.

    Args:
        collection: The ChromaDB collection object.
        legislation_id (int): The primary key from the SQL database.
        text_content (str): The original text content (for retrieval).
        embedding (list): The generated embedding vector.
    """
    try:
        # ChromaDB requires string IDs for documents
        doc_id = str(legislation_id)
        collection.add(
            documents=[text_content],
            embeddings=[embedding],
            metadatas=[{"sql_id": legislation_id}], # Store SQL ID as metadata
            ids=[doc_id]
        )
        print(f"Added document {doc_id} to ChromaDB.")
    except Exception as e:
        print(f"Error adding document {legislation_id} to ChromaDB: {e}")

def query_vectordb(collection, query_embedding, n_results=4):
    """
    Queries the ChromaDB collection for semantically similar results.

    Args:
        collection: The ChromaDB collection object.
        query_embedding (list): The embedding of the query text.
        n_results (int): Number of top results to retrieve.

    Returns:
        list: A list of dicts, each containing 'document', 'metadata', 'distance'.
    """
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    # The results format is a bit nested. Extract relevant info.
    # It returns lists for each query, so [0] for the first query.
    
    # Structure of results: {'ids': [[]], 'embeddings': [[]], 'documents': [[]], 'metadatas': [[]], 'distances': [[]]}
    
    retrieved_docs = []
    if results and results['ids'] and results['ids'][0]:
        for i in range(len(results['ids'][0])):
            retrieved_docs.append({
                'id': results['ids'][0][i],
                'document': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] # Cosine distance
            })
    return retrieved_docs


if __name__ == '__main__':
    # Example usage:
    client = get_chroma_client()
    collection = get_legislation_collection(client)

    # Need to load embedding model to get sample embeddings
    from etl.embeddings import load_embedding_model, generate_embedding
    
    embedding_model = load_embedding_model()

    # Add some dummy data
    sample_text_1 = "This is a law about environmental protection and pollution control."
    sample_emb_1 = generate_embedding(embedding_model, sample_text_1)
    add_embedding_to_vectordb(collection, 1, sample_text_1, sample_emb_1)

    sample_text_2 = "A new regulation regarding financial services and banking."
    sample_emb_2 = generate_embedding(embedding_model, sample_text_2)
    add_embedding_to_vectordb(collection, 2, sample_text_2, sample_emb_2)
    
    sample_text_3 = "The Act focuses on planning applications and urban development."
    sample_emb_3 = generate_embedding(embedding_model, sample_text_3)
    add_embedding_to_vectordb(collection, 3, sample_text_3, sample_emb_3)

    # Query
    query_text = "rules on town planning and construction"
    query_emb = generate_embedding(embedding_model, query_text)

    print(f"\nQuerying for: '{query_text}'")
    results = query_vectordb(collection, query_emb)

    print("\n--- Top 4 Semantically Similar Results ---")
    for res in results:
        print(f"SQL ID: {res['metadata']['sql_id']}, Distance: {res['distance']:.4f}")
        print(f"Document (first 100 chars): {res['document'][:100]}...")
        print("-" * 30)

    # You can also get the count of documents
    print(f"\nTotal documents in ChromaDB: {collection.count()}")