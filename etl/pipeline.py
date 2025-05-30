import os
import time
from datetime import datetime

# Import functions from your other modules
from etl.scraper import get_legislation_links, download_legislation_html
from etl.cleaner import clean_legislation_html, extract_metadata
from etl.database import get_db_engine, create_tables, get_db_session, insert_legislation, Legislation
from etl.embeddings import load_embedding_model, generate_embedding
from etl.vector_db import get_chroma_client, get_legislation_collection, add_embedding_to_vectordb

def run_etl_pipeline():
    """
    Orchestrates the entire ETL pipeline: scraping, cleaning, metadata extraction,
    storing in SQL DB, generating embeddings, and storing in Vector DB.
    Includes basic checkpointing for resilience.
    """
    # --- Configuration from Environment Variables ---
    legislation_year = int(os.getenv("LEGISLATION_YEAR", "2024"))
    legislation_month = os.getenv("LEGISLATION_MONTH", "August") # Used for filtering later
    legislation_category = os.getenv("LEGISLATION_CATEGORY", "planning") # Used for filtering later

    print(f"--- Starting ETL Pipeline for {legislation_category} legislation from {legislation_month}/{legislation_year} ---")

    # --- Initialize Databases and Embedding Model ---
    try:
        sql_engine = get_db_engine()
        create_tables(sql_engine) # Ensure SQL tables exist
        sql_session = get_db_session() # Get a new session for this pipeline run

        chroma_client = get_chroma_client()
        chroma_collection = get_legislation_collection(chroma_client)

        embedding_model = load_embedding_model()
        if not embedding_model:
            print("Error: Could not load embedding model. Exiting pipeline.")
            return # Exit if model fails to load
    except Exception as e:
        print(f"Initialisation error: {e}")
        return # Exit if any setup fails

    # --- Scraping Phase ---
    print(f"\n--- Phase 1: Scraping Legislation Links for {legislation_year} ---")
    all_links = get_legislation_links(year=legislation_year) # This needs refinement for month/category
    if not all_links:
        print("No legislation links found for the specified year. Exiting pipeline.")
        sql_session.close()
        return

    print(f"Identified {len(all_links)} potential legislation links.")

    # --- Processing Loop (with checkpointing and error handling) ---
    processed_count = 0
    start_time = time.time()

    for i, url in enumerate(all_links):
        print(f"\nProcessing link {i+1}/{len(all_links)}: {url}")
        
        # Checkpoint 1: Check if this URL (or its derived identifier) is already fully processed
        # This prevents reprocessing from scratch if a crash occurs.
        existing_legislation = sql_session.query(Legislation).filter_by(source_url=url).first()
        if existing_legislation and existing_legislation.status == 'embedded':
            print(f"  Legislation from {url} already fully processed. Skipping.")
            processed_count += 1
            continue
        
        # Determine the start point for reprocessing if status is not 'embedded'
        current_status = existing_legislation.status if existing_legislation else 'new'
        print(f"  Current status for {url}: {current_status}")

        try:
            # --- Download HTML ---
            html_content = None
            if current_status == 'new' or current_status == 'failed_download':
                print(f"  Downloading HTML for {url}...")
                html_content = download_legislation_html(url)
                if not html_content:
                    print(f"  Failed to download HTML for {url}. Marking as failed_download and skipping.")
                    if existing_legislation:
                        existing_legislation.status = 'failed_download'
                        sql_session.add(existing_legislation)
                        sql_session.commit()
                    continue # Skip to next URL

            # --- Clean Data & Extract Metadata ---
            # If html_content is None, means it was already downloaded and we are resuming
            # For simplicity, we'll re-download/re-process for now if not 'embedded'
            # A more robust system would save raw HTML to disk.
            if not html_content:
                 # In a robust system, you'd reload the raw HTML here
                 # For this example, we assume if not embedded, we re-download.
                 html_content = download_legislation_html(url)
                 if not html_content:
                     print(f"  Failed to re-download HTML for {url} during resume. Skipping.")
                     continue
            
            print(f"  Cleaning HTML and extracting metadata for {url}...")
            cleaned_text = clean_legislation_html(html_content)
            metadata = extract_metadata(html_content)

            # Filter by month and category here if scraper couldn't do it directly
            # This is a placeholder for your actual filtering logic.
            # You'd need to parse the dates from 'metadata.date_made' and compare.
            # Also, check `cleaned_text` or `metadata['title']` for 'planning' keywords.
            # This logic needs careful implementation based on your data.
            # Example (simplified):
            # if legislation_month.lower() not in metadata.get('date_made', '').lower():
            #     print(f"  Skipping {url}: Does not match month '{legislation_month}'.")
            #     continue
            # if legislation_category.lower() not in cleaned_text.lower() and \
            #    legislation_category.lower() not in metadata.get('title', '').lower():
            #     print(f"  Skipping {url}: Does not match category '{legislation_category}'.")
            #     continue

            if not metadata.get('title') or not metadata.get('identifier'):
                print(f"  Skipping {url} due to missing essential metadata (title/identifier).")
                continue # Skip if critical metadata is missing

            # --- Store/Update in SQL DB ---
            # Prepare data for SQL DB
            data_to_db = {
                'title': metadata.get('title'),
                'identifier': metadata.get('identifier'),
                'type': metadata.get('type'),
                'date_made': metadata.get('date_made'),
                'effective_date': metadata.get('effective_date'),
                'source_url': url,
                'content': cleaned_text,
                'metadata_json': metadata # Store all metadata as JSON for flexibility
            }
            legislation_entry = insert_legislation(sql_session, data_to_db) # This function handles insert/update
            if not legislation_entry:
                print(f"  Failed to insert/update SQL entry for {url}. Skipping.")
                continue

            # Update status in DB (e.g., 'cleaned') after successful parsing and SQL store
            legislation_entry.status = 'cleaned'
            sql_session.add(legislation_entry)
            sql_session.commit()
            print(f"  SQL DB updated for {legislation_entry.identifier}.")

            # --- Generate Embedding ---
            if current_status != 'embedded': # Only generate if not already embedded
                print(f"  Generating embedding for {legislation_entry.identifier}...")
                embedding = generate_embedding(embedding_model, cleaned_text)
                if not embedding:
                    print(f"  Failed to generate embedding for {legislation_entry.identifier}. Marking as failed_embedding.")
                    legislation_entry.status = 'failed_embedding'
                    sql_session.add(legislation_entry)
                    sql_session.commit()
                    continue

                # --- Store in Vector DB ---
                print(f"  Adding embedding to ChromaDB for {legislation_entry.identifier} (SQL ID: {legislation_entry.id})...")
                add_embedding_to_vectordb(chroma_collection, legislation_entry.id, cleaned_text, embedding)

                # Final status update in SQL DB
                legislation_entry.status = 'embedded'
                legislation_entry.processed_at = datetime.utcnow()
                sql_session.add(legislation_entry)
                sql_session.commit()
                print(f"  Successfully processed and embedded {legislation_entry.identifier}.")
            else:
                print(f"  {legislation_entry.identifier} already embedded. Skipping embedding step.")

            processed_count += 1
            # Log performance every 100 entries (adjust interval as needed)
            if processed_count % 100 == 0:
                elapsed_time = time.time() - start_time
                time_per_100_entries = elapsed_time / processed_count * 100
                print(f"--- Processed {processed_count} entries. Time per 100 entries: {time_per_100_entries:.2f} seconds. ---")

        except Exception as e:
            # Catch any unexpected errors during processing a single item
            sql_session.rollback() # Rollback any partial transaction for the current item
            print(f"  !!! An unexpected error occurred while processing {url}: {e}")
            if existing_legislation:
                existing_legislation.status = 'failed_pipeline' # Mark as general failure
                sql_session.add(existing_legislation)
                sql_session.commit()
            else:
                print("  (Could not update status as no existing SQL entry found)")
            # Continue to the next URL, allowing the pipeline to recover.
            pass # Keep pipeline running for other items

        finally:
            # Be respectful of the website's servers
            time.sleep(0.5)

    sql_session.close()
    print(f"\n--- ETL Pipeline finished. Total processed: {processed_count} entries. ---")

if __name__ == '__main__':
    run_etl_pipeline()