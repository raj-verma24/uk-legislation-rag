# cli/query.py
import argparse
import sys
import os

# Add parent directory to path to allow imports from etl/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from etl.embeddings import load_embedding_model, generate_embedding
from etl.vector_db import get_chroma_client, get_legislation_collection
from etl.database import get_db_session, Legislation # To retrieve full legislation details from SQL DB

def main():
    parser = argparse.ArgumentParser(description="Query UK Legislation dataset for semantically similar results.")
    parser.add_argument("query_string", type=str, help="The query string to search for.")
    args = parser.parse_args()

    print("Initializing components for query...")
    
    # Load embedding model
    embedding_model = load_embedding_model()
    if not embedding_model:
        print("Failed to load embedding model. Exiting.")
        sys.exit(1)

    # Get ChromaDB client and collection
    chroma_client = get_chroma_client()
    legislation_collection = get_legislation_collection(chroma_client)
    
    # Get SQL DB session
    sql_session = get_db_session()

    print(f"Generating embedding for query: '{args.query_string}'")
    query_embedding = generate_embedding(embedding_model, args.query_string)
    if not query_embedding:
        print("Failed to generate embedding for the query. Exiting.")
        sql_session.close()
        sys.exit(1)

    print("Querying vector database...")
    results = legislation_collection.query(
        query_embeddings=[query_embedding],
        n_results=4, # As per requirement
        include=['documents', 'metadatas', 'distances']
    )

    print("\n--- Top 4 Semantically Similar Results (from Vector DB) ---")
    if not results or not results['ids'] or not results['ids'][0]:
        print("No results found.")
    else:
        # results['ids'][0] contains the list of IDs from ChromaDB
        # results['documents'][0] contains the text content
        # results['metadatas'][0] contains the metadata (including sql_id)
        # results['distances'][0] contains the cosine distance
        
        # Sort by distance (smaller distance means more similar)
        sorted_results = sorted([
            {
                'id': results['ids'][0][i],
                'document': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i]
            } for i in range(len(results['ids'][0]))
        ], key=lambda x: x['distance'])

        for i, res in enumerate(sorted_results):
            sql_id = res['metadata'].get('sql_id')
            print(f"\nResult {i+1} (Distance: {res['distance']:.4f}):")
            print(f"Chroma DB ID: {res['id']}")
            print(f"Content snippet: {res['document'][:200]}...") # Show a snippet

            if sql_id:
                # Retrieve full details from SQL database using sql_id
                legislation_details = sql_session.query(Legislation).filter_by(id=sql_id).first()
                if legislation_details:
                    print(f"  SQL Legislation Title: {legislation_details.title}")
                    print(f"  SQL Legislation Identifier: {legislation_details.identifier}")
                    print(f"  Source URL: {legislation_details.source_url}")
                else:
                    print(f"  No full legislation details found in SQL DB for ID: {sql_id}")
            else:
                print("  No SQL ID found in metadata.")
            print("-" * 50)
            
    sql_session.close()

if __name__ == "__main__":
    main()