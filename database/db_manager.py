import duckdb
import os
import logging

# Configure enterprise-grade logging instead of simple print statements
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DatabaseManager:
    def __init__(self, db_path: str = "database/job_intelligence.duckdb"):
        """
        Initializes the database connection.
        Using a local file-based DuckDB instance for high-performance analytical queries.
        """
        self.db_path = db_path
        self._initialize_schema()

    def _get_connection(self):
        """Creates and returns a connection to the DuckDB instance."""
        return duckdb.connect(self.db_path)

    def _initialize_schema(self):
        """
        Executes DDL (Data Definition Language) statements to create the Star Schema.
        This includes dimensional tables for Jobs/Candidates and a fact table for Match results.
        """
        try:
            with self._get_connection() as conn:
                # Dimension Table: Jobs (Stores scraped market data)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS dim_jobs (
                        job_id VARCHAR PRIMARY KEY,
                        job_title VARCHAR NOT NULL,
                        company_name VARCHAR,
                        job_description TEXT NOT NULL,
                        extracted_skills VARCHAR[],
                        posted_date DATE,
                        ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # Dimension Table: Candidates (Stores user profiles and CV text)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS dim_candidates (
                        candidate_id VARCHAR PRIMARY KEY,
                        candidate_name VARCHAR,
                        cv_text TEXT NOT NULL,
                        extracted_skills VARCHAR[],
                        upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # Fact Table: Job Matches (Stores the AI analytical output)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS fact_job_matches (
                        match_id VARCHAR PRIMARY KEY,
                        candidate_id VARCHAR,
                        job_id VARCHAR,
                        match_score_percentage DECIMAL(5,2),
                        missing_keywords VARCHAR[],
                        matching_keywords VARCHAR[],
                        analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (candidate_id) REFERENCES dim_candidates(candidate_id),
                        FOREIGN KEY (job_id) REFERENCES dim_jobs(job_id)
                    );
                """)
            logging.info("Database Star Schema initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize database schema: {e}")
            raise

# For testing purposes when running this specific file
if __name__ == "__main__":
    db = DatabaseManager()