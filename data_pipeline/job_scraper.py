import pandas as pd
import uuid
from datetime import datetime
import logging
import sys
import os

# Add the root directory to the system path to import database modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db_manager import DatabaseManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class JobDataPipeline:
    def __init__(self):
        """
        Initializes the ETL Pipeline.
        Connects to the DuckDB instance to load the transformed data.
        """
        self.db = DatabaseManager()

    def extract_mock_jobs(self) -> list[dict]:
        """
        Simulates data extraction from job boards (e.g., LinkedIn, Indeed).
        In a full production environment, this would use requests/BeautifulSoup or official APIs.
        """
        logging.info("Starting data extraction phase...")
        return [
            {
                "job_title": "Data Engineer",
                "company_name": "TechFlow Systems",
                "job_description": "Looking for a Data Engineer skilled in Python, SQL, and Pandas to build scalable ETL pipelines.",
                "posted_date": "2026-06-20"
            },
            {
                "job_title": "AI Specialist",
                "company_name": "Visionary AI",
                "job_description": "Seeking an AI professional to develop intelligent agents. Must know Python, LLMs, and vector search.",
                "posted_date": "2026-06-21"
            }
        ]

    def transform_data(self, raw_data: list[dict]) -> pd.DataFrame:
        """
        Transforms raw extracted data using Pandas.
        Cleans text, handles missing values, and generates unique IDs.
        """
        logging.info("Transforming raw data into structured DataFrame...")
        df = pd.DataFrame(raw_data)
        
        # Generate unique UUIDs for primary keys
        df['job_id'] = [str(uuid.uuid4()) for _ in range(len(df))]
        
        # Clean string columns (strip whitespace, upper/lower case normalization if needed)
        df['job_title'] = df['job_title'].str.strip()
        df['company_name'] = df['company_name'].str.strip()
        
        # Convert date strings to datetime objects
        df['posted_date'] = pd.to_datetime(df['posted_date']).dt.date
        
        # Placeholder for basic keyword extraction (AI Agent will do the advanced extraction later)
        df['extracted_skills'] = df['job_description'].apply(
            lambda x: ['Python', 'SQL'] if 'Python' in x else []
        )
        
        return df

    def load_to_duckdb(self, df: pd.DataFrame):
        """
        Loads the transformed Pandas DataFrame directly into the DuckDB dimensional table.
        """
        logging.info("Loading transformed data into DuckDB warehouse...")
        try:
            with self.db._get_connection() as conn:
                # DuckDB natively supports querying Pandas DataFrames directly!
                conn.execute("""
                    INSERT INTO dim_jobs (job_id, job_title, company_name, job_description, extracted_skills, posted_date)
                    SELECT job_id, job_title, company_name, job_description, extracted_skills, posted_date 
                    FROM df
                """)
            logging.info(f"Successfully loaded {len(df)} jobs into the database.")
        except Exception as e:
            logging.error(f"Failed to load data to warehouse: {e}")
            raise

    def run_pipeline(self):
        """Executes the complete ETL workflow."""
        raw_jobs = self.extract_mock_jobs()
        transformed_df = self.transform_data(raw_jobs)
        self.load_to_duckdb(transformed_df)

if __name__ == "__main__":
    pipeline = JobDataPipeline()
    pipeline.run_pipeline()