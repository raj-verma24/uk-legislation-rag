# Use a slim Python 3.12 base image
FROM python:3.12-slim

# Set environment variables for non-interactive operations and Python unbuffered output
ENV PYTHONUNBUFFERED 1 \
    DEBIAN_FRONTEND=noninteractive

# Install build dependencies for sqlite3 and other common tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libsqlite3-dev \
    libpq-dev \
    gnupg \
    wget \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Crucial: Upgrade pip before installing requirements (still good practice)
RUN pip install --upgrade pip

# Compile and install a newer version of SQLite3
# ChromaDB requires >= 3.35.0. Let's use a recent stable version (e.g., 3.45.2) and a reliable download path.
ENV SQLITE_VERSION 3450200

# Corrected RUN command - removed the comment from the wget line
RUN wget https://www.sqlite.org/2024/sqlite-autoconf-$SQLITE_VERSION.tar.gz && \
    tar -xzf sqlite-autoconf-$SQLITE_VERSION.tar.gz && \
    cd sqlite-autoconf-$SQLITE_VERSION && \
    ./configure --prefix=/usr/local && \
    make && \
    make install && \
    ldconfig && \
    cd .. && \
    rm -rf sqlite-autoconf-$SQLITE_VERSION sqlite-autoconf-$SQLITE_VERSION.tar.gz

# Set environment variables to ensure Python uses the newly installed sqlite3
ENV LD_LIBRARY_PATH /usr/local/lib:$LD_LIBRARY_PATH
ENV PKG_CONFIG_PATH /usr/local/lib/pkgconfig:$PKG_CONFIG_PATH

# Set working directory inside the container
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directories for models and DBs inside the container
RUN mkdir -p /app/models /app/db/vector

# Copy the entire application code into the container
COPY . .

# Set default environment variables (can be overridden during docker run or in docker-compose)
ENV DATABASE_URL="postgresql://user:password@postgres_db:5432/legislation_db" \
    CHROMA_DB_PATH="/app/db/vector" \
    MODEL_PATH="/app/models/all-MiniLM-L6-v2" \
    LEGISLATION_YEAR="2024" \
    LEGISLATION_MONTH="August" \
    LEGISLATION_CATEGORY="planning"

# Copy and make the entrypoint script executable
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Define the entrypoint script that will be executed when the container starts
ENTRYPOINT ["docker-entrypoint.sh"]

# Default command (will be overridden by docker-compose)
CMD ["pipeline"]