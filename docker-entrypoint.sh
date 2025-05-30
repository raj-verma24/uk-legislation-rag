#!/bin/bash
set -e

# Function to wait for PostgreSQL to be ready
wait_for_postgres() {
  echo "Waiting for PostgreSQL to be ready..."
  # 'db' is the service name for PostgreSQL in docker-compose.yml
  until pg_isready -h db -p 5432 -U user; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
  done
  echo "PostgreSQL is up and running!"
}

# Function to ensure ChromaDB directory exists for persistent client
ensure_chroma_ready() {
  echo "Ensuring ChromaDB data directory exists..."
  mkdir -p "$CHROMA_DB_PATH"
  echo "ChromaDB data directory ready: $CHROMA_DB_PATH"
}

# This script acts as a flexible entrypoint for our Docker image.
# It can either run the ETL pipeline or the CLI query application.

if [ "$1" = "pipeline" ]; then
  # If the first argument is "pipeline", run the ETL process.
  echo "Starting ETL Pipeline..."
  wait_for_postgres # Wait for the PostgreSQL service to be ready
  ensure_chroma_ready # Ensure the ChromaDB data directory is prepared
  python etl/pipeline.py # Execute the main ETL pipeline script
elif [ "$1" = "query" ]; then
  # If the first argument is "query", run the CLI query application.
  echo "Starting CLI Query Application..."
  shift # Remove the 'query' argument so that "$@" passes the actual query string
  # Ensure the embedding model is loaded/downloaded before querying (first time only)
  # This makes the query script robust even if the model wasn't pre-downloaded or persisted.
  python -c "from etl.embeddings import load_embedding_model; load_embedding_model()"
  python cli/query.py "$@" # Execute the CLI query script, passing remaining arguments
else
  # If no specific command or an unknown command is given, execute passed arguments directly.
  exec "$@"
fi