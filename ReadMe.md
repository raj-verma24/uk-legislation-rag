UK Legislation RAG System
1. Project Overview
This project implements a Retrieval-Augmented Generation (RAG) system for UK legislation. It focuses on building an Extract, Transform, Load (ETL) pipeline to scrape, clean, and vectorize legislation documents, storing them in both a traditional SQL database and a vector database. A command-line interface (CLI) application then allows users to perform semantic searches on the vectorized legislation and retrieve relevant passages.

The system aims to provide a robust framework for accessing and querying legal texts, making it easier to find information based on semantic similarity rather than just keywords.

2. Features
Legislation Scraping: Extracts legislation text from legislation.gov.uk.
Data Cleaning: Processes raw HTML to extract meaningful text and metadata.
SQL Database Storage: Stores structured legislation data (title, identifier, content, metadata) in PostgreSQL.
Text Embedding: Converts legislation text into dense vector representations using a Sentence-Transformer model (all-MiniLM-L6-v2).
Vector Database Storage: Stores text embeddings in ChromaDB for efficient semantic search.
CLI Semantic Search: Allows users to query the legislation database using natural language, returning the most semantically similar passages.
Dockerized Environment: All components are containerized using Docker and Docker Compose for easy setup, consistent environments, and portability.
3. Project Structure
Okay, I've reviewed your README.md content. The main issue for the project structure is that it's just plain text, not formatted as a code block, and the "Bash" and "YAML" labels are also not part of proper Markdown code block syntax.

I've made the necessary formatting corrections and added a few minor improvements for clarity and emphasis.

Here's the revised README.md content for you to use:

Markdown

# UK Legislation RAG System

## 1. Project Overview
This project implements a Retrieval-Augmented Generation (RAG) system for UK legislation. It focuses on building an Extract, Transform, Load (ETL) pipeline to scrape, clean, and vectorize legislation documents, storing them in both a traditional SQL database and a vector database. A command-line interface (CLI) application then allows users to perform semantic searches on the vectorized legislation and retrieve relevant passages.

The system aims to provide a robust framework for accessing and querying legal texts, making it easier to find information based on semantic similarity rather than just keywords.

## 2. Features
* **Legislation Scraping:** Extracts legislation text from `legislation.gov.uk`.
* **Data Cleaning:** Processes raw HTML to extract meaningful text and metadata.
* **SQL Database Storage:** Stores structured legislation data (title, identifier, content, metadata) in PostgreSQL.
* **Text Embedding:** Converts legislation text into dense vector representations using a Sentence-Transformer model (`all-MiniLM-L6-v2`).
* **Vector Database Storage:** Stores text embeddings in ChromaDB for efficient semantic search.
* **CLI Semantic Search:** Allows users to query the legislation database using natural language, returning the most semantically similar passages.
* **Dockerized Environment:** All components are containerized using Docker and Docker Compose for easy setup, consistent environments, and portability.

## 3. Project Structure
.
├── cli/
│   ├── init.py
│   └── query.py           # CLI application for semantic search
├── db/
│   ├── sql/               # Placeholder for local SQLite (if used)
│   └── vector/            # Persistent storage for ChromaDB data
├── etl/
│   ├── init.py
│   ├── cleaner.py         # Cleans HTML and extracts metadata
│   ├── database.py        # Handles SQL database interactions (PostgreSQL)
│   ├── embeddings.py      # Manages embedding model loading and generation
│   ├── pipeline.py        # Orchestrates the ETL process
│   ├── scraper.py         # Scrapes legislation links and HTML content
│   └── vector_db.py       # Handles Vector DB interactions (ChromaDB)
├── models/                # Persistent storage for the Sentence-Transformer model
├── Dockerfile             # Defines the Docker image for the application
├── docker-compose.yml     # Orchestrates Docker services (app, db)
├── docker-entrypoint.sh   # Entrypoint script for Docker container commands
└── requirements.txt       # Python dependencies

## 4. Technologies Used
* Python 3.12+
* Docker & Docker Compose
* PostgreSQL: Relational database for structured legislation data.
* ChromaDB: Vector database for storing and searching embeddings.
* `requests` & `BeautifulSoup4`: For web scraping.
* `sentence-transformers`: For generating text embeddings (`all-MiniLM-L6-v2` model).
* `SQLAlchemy`: ORM for database interactions.
* `psycopg2-binary`: PostgreSQL adapter for Python.
* `Typer` (Optional, for advanced CLI): Used for building the CLI (though `argparse` or basic `sys.argv` could also be used).

## 5. Setup and Installation

### Prerequisites
Before you begin, ensure you have the following installed on your system:
* **Python 3.12.x (or 3.9+):** Download from [python.org](https://www.python.org/). Make sure to add it to your system PATH during installation.
* **Git:** Download from [git-scm.com](https://git-scm.com/).
* **Docker Desktop for Windows:** Download from [docker.com](https://www.docker.com/products/docker-desktop/). Ensure WSL 2 is enabled and configured correctly.

### Local Development Setup (Recommended for coding and debugging)

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/your-repo-name.git](https://github.com/YOUR_USERNAME/your-repo-name.git) # Replace with your actual repo URL
    cd your-repo-name # Navigate into the cloned directory
    ```

2.  **Create and activate a Python virtual environment:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate.bat   # For Command Prompt
    # .\venv\Scripts\activate      # For PowerShell (if execution policy allows)
    # source venv/bin/activate    # For Linux/macOS
    ```

3.  **Upgrade pip and essential packaging tools:**
    ```bash
    pip install --upgrade pip setuptools wheel
    ```

4.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Start the PostgreSQL database via Docker Compose:**
    In a **separate terminal or command prompt window** (keep it running), navigate to your project root and start only the database service:
    ```bash
    docker-compose up db
    ```
    Ensure the `db` service is healthy before proceeding.

6.  **Run ETL pipeline locally (for testing):**
    Once the database is up and running in the separate terminal, you can run your pipeline directly from your activated `venv`:
    ```bash
    python etl/pipeline.py
    ```

7.  **Run CLI query locally (for testing):**
    After the pipeline completes:
    ```bash
    python cli/query.py "What are the rules regarding planning permission for extensions?"
    ```
    (Replace with your desired query.)

### Dockerized Setup (For building and running the complete system)

1.  Ensure Docker Desktop is running.

2.  **Navigate to your project root:**
    ```bash
    cd C:\Projects\uk-legislation-rag # Or the equivalent path on your system
    ```

3.  **Build Docker images:**
    This will build the `app` image and set up the `db` service. The first time might take a while as it downloads base images and the embedding model.
    ```bash
    docker-compose build
    ```

4.  **Run the ETL pipeline:**
    This will start both the PostgreSQL and application containers. The app container will execute the ETL process.
    ```bash
    docker-compose up app
    ```
    Monitor the logs in your terminal. The process might take some time depending on the amount of legislation scraped and processed.

5.  **Run a semantic search query:**
    Once the ETL pipeline has successfully completed and populated the databases:

    **Option A (Modify `docker-compose.yml`):**
    Edit your `docker-compose.yml` file and change the `command` for the `app` service to run the query instead of the pipeline:
    ```yaml
        app:
          # ...
          command: ["query", "liability to a high income child benefit charge"] # Replace with your query
    ```
    Save the file, then run:
    ```bash
    docker-compose up app
    ```

    **Option B (Direct Docker run - useful for quick, one-off queries):**
    First, stop any running `docker-compose up` (Ctrl+C).
    Then, execute the command directly on the built image:
    ```bash
    docker run --rm legislation_etl_cli_app query "liability to a high income child benefit charge"
    ```
    (Replace `legislation_etl_cli_app` if your image name is different, and your query string).

## 6. How to Use

### ETL Pipeline
The ETL pipeline is designed to be run once initially to populate the databases. It can also be re-run to update existing or add new legislation data.

* **To run ETL locally:** `python etl/pipeline.py` (after setting up local DB)
* **To run ETL via Docker:** Ensure `command: ["pipeline"]` is set for the `app` service in `docker-compose.yml`, then run `docker-compose up app`.

### Semantic Search CLI
After the data is loaded into the vector database, you can use the CLI for semantic search.

* **To query locally:** `python cli/query.py "Your search query"`
* **To query via Docker:** Adjust `docker-compose.yml` command or use `docker run` as described in the Dockerized Setup section.

**Example Query:**
```bash
# Locally
python cli/query.py "What are the environmental impact assessment requirements for new construction?"

# Via Docker
docker run --rm legislation_etl_cli_app query "What are the environmental impact assessment requirements for new construction?"
The CLI will return the top N (currently 4) semantically similar results, including snippets of the text, title, identifier, and source URL.

7. Configuration
Environmental variables are used for configuration:

DATABASE_URL: Connection string for PostgreSQL (e.g., postgresql://user:password@db:5432/legislation_db).
CHROMA_DB_PATH: Path where ChromaDB stores its data (e.g., /app/db/vector inside Docker).
MODEL_PATH: Path where the Sentence-Transformer model is stored (e.g., /app/models/all-MiniLM-L6-v2 inside Docker).
LEGISLATION_YEAR: Year to scrape legislation from (default: 2024).
LEGISLATION_MONTH: Month to filter legislation by (default: August).
LEGISLATION_CATEGORY: Category to filter legislation by (default: planning).
These variables can be set in your .env file (Docker Compose picks this up automatically if present), or directly in your docker-compose.yml or CLI calls.

8. Potential Improvements & Next Steps
Robust Scraping: Implement more sophisticated scraping logic for legislation.gov.uk to handle diverse document structures, pagination, and filtering more precisely (e.g., by type of legislation, exact date ranges).
Error Handling and Logging: Enhance error handling in the ETL pipeline with more detailed logging and retry mechanisms.
Advanced Text Chunking: Explore different text chunking strategies (e.g., recursive character text splitter) to optimize context for embedding and retrieval.
API Integration (if available): If legislation.gov.uk provides a formal API, switch from web scraping to API calls for more stable and structured data retrieval.
UI/Frontend: Develop a simple web interface (e.g., with Flask or FastAPI) to provide a more user-friendly search experience.
Evaluation Metrics: Implement metrics to evaluate the effectiveness of the RAG system (e.g., retrieval precision, recall).
Model Selection: Experiment with different embedding models.
Deployment: Deploy the system to a cloud platform (AWS, Azure, GCP).
