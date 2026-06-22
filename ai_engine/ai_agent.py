import os
import json
import logging
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables (like API keys) from the .env file
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class JobMatchAgent:
    def __init__(self):
        """
        Initializes the AI Agent.
        Enforces enterprise standards by implementing a fallback (mock) mechanism 
        if the API key is not present, avoiding application crashes during local testing.
        """
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logging.warning("OPENAI_API_KEY is missing. Agent will run in Mock Mode for testing.")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key)

    def analyze_cv_against_job(self, cv_text: str, job_desc: str) -> dict:
        """
        Uses an LLM (OpenAI) to perform deep semantic matching between the CV and Job Description.
        Strictly returns a structured JSON object to be easily parsed by the UI and Database.
        """
        if not self.client:
            # Fallback mock data for testing the Data Engineering pipeline safely
            return {
                "match_score": 75,
                "matching_keywords": ["Python", "SQL", "Pandas", "Data Engineering"],
                "missing_keywords": ["Airflow", "Cloud Architecture", "Docker"],
                "ats_suggestions": "Quantify your achievements in the ETL pipeline projects."
            }

        prompt = f"""
        You are an expert Enterprise ATS (Applicant Tracking System) and AI Recruiter.
        Analyze the following CV against the given Job Description.
        Extract the following information and return ONLY a valid JSON object:
        - match_score: (integer between 0 and 100 based on core skills and experience)
        - matching_keywords: (list of strings representing found technical skills)
        - missing_keywords: (list of strings representing required skills missing from the CV)
        - ats_suggestions: (string, 1-2 sentences of actionable advice to improve the CV for this specific job)

        CV Text:
        {cv_text}

        Job Description:
        {job_desc}
        """

        try:
            logging.info("Sending prompt to AI for semantic parsing and analysis...")
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo", # Using 3.5 for speed and cost-efficiency in parsing
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}, # Strictly enforce JSON output
                temperature=0.1 # Low temperature for analytical consistency
            )
            
            result_json = json.loads(response.choices[0].message.content)
            logging.info("AI Analysis completed and JSON parsed successfully.")
            return result_json
            
        except Exception as e:
            logging.error(f"AI Agent inference failed: {e}")
            raise

# For testing the module independently
if __name__ == "__main__":
    agent = JobMatchAgent()
    mock_cv = "I am a Data Engineer with 2 years of experience in Python, Pandas, and SQL."
    mock_job = "We need a Data Engineer skilled in Python, SQL, and Docker."
    
    result = agent.analyze_cv_against_job(mock_cv, mock_job)
    print(json.dumps(result, indent=2))