# etl/database.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from datetime import datetime

# Define your PostgreSQL connection string
# It's recommended to use environment variables for sensitive info
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/legislation_db")

Base = declarative_base()

class Legislation(Base):
    __tablename__ = 'legislations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    identifier = Column(String, unique=True, nullable=False) # e.g., "2024 No. 76"
    legislation_type = Column(String) # e.g., "Statutory Instrument", "Public General Act"
    date_made = Column(String) # Store as string for flexibility, convert to Date if needed later
    effective_date = Column(String)
    source_url = Column(String, unique=True, nullable=False)
    content = Column(Text, nullable=False) # Cleaned text
    metadata_json = Column(JSON) # Store any additional extracted metadata as JSON

    # Add columns for tracking processing status for resiliency
    processed_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default='pending') # pending, scraped, cleaned, embedded, failed

    def __repr__(self):
        return f"<Legislation(title='{self.title}', identifier='{self.identifier}')>"

def get_db_engine():
    """Returns a SQLAlchemy engine."""
    return create_engine(DATABASE_URL)

def create_tables(engine):
    """Creates all tables defined in the Base metadata."""
    Base.metadata.create_all(engine)
    print("SQL tables created or already exist.")

def get_db_session():
    """Returns a new SQLAlchemy session."""
    engine = get_db_engine()
    Session = sessionmaker(bind=engine)
    return Session()

def insert_legislation(session, data):
    """
    Inserts or updates a legislation entry in the database.
    'data' should be a dictionary with keys matching Legislation model attributes.
    """
    # Check if entry already exists based on identifier or source_url
    existing_legislation = session.query(Legislation).filter_by(identifier=data['identifier']).first()
    if existing_legislation:
        # Update existing entry if needed, or skip if already processed
        # For simplicity, let's assume we skip if already exists for now.
        # In a real pipeline, you might update 'content' or 'status'.
        print(f"Legislation with identifier {data['identifier']} already exists. Skipping insertion.")
        return existing_legislation
    else:
        legislation_entry = Legislation(
            title=data['title'],
            identifier=data['identifier'],
            legislation_type=data.get('type'),
            date_made=data.get('date_made'),
            effective_date=data.get('effective_date'),
            source_url=data['source_url'],
            content=data['content'],
            metadata_json=data.get('metadata', {}),
            status='cleaned' # Initial status after cleaning and before embedding
        )
        session.add(legislation_entry)
        session.commit()
        print(f"Inserted legislation: {legislation_entry.title}")
        return legislation_entry

if __name__ == '__main__':
    # Example usage:
    engine = get_db_engine()
    create_tables(engine) # Ensure tables are created

    # Example data (would come from cleaner.py)
    sample_data = {
        'title': 'The Test Statutory Instrument 2024',
        'identifier': '2024 No. 999',
        'type': 'Statutory Instrument',
        'date_made': '1st August 2024',
        'effective_date': '1st September 2024',
        'source_url': 'https://www.legislation.gov.uk/uksi/2024/999/made/data.htm',
        'content': 'This is the cleaned content of the test statutory instrument...',
        'metadata': {'some_extra_field': 'value'}
    }

    session = get_db_session()
    try:
        inserted_entry = insert_legislation(session, sample_data)
        if inserted_entry:
            print(f"Successfully inserted/found: {inserted_entry.id}")

        # You can query data
        all_legislations = session.query(Legislation).all()
        print("\nAll legislations in DB:")
        for leg in all_legislations:
            print(f"- {leg.identifier}: {leg.title} (Status: {leg.status})")

    except Exception as e:
        session.rollback()
        print(f"An error occurred during DB operation: {e}")
    finally:
        session.close()