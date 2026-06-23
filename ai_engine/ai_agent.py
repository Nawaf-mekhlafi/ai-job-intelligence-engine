import os
import json
import logging
import random
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class JobMatchAgent:
    def __init__(self):
        """
        Initializes the Production AI Agent with an Enterprise API Key Rotation Pool.
        This prevents app crashes by automatically swapping exhausted API keys.
        """
        # Load all available keys from environment variables
        self.pool = []
        for i in range(1, 10): # Supports up to 9 backup keys (GROQ_API_KEY_1 to 9)
            key = os.environ.get(f"GROQ_API_KEY_{i}")
            if key:
                self.pool.append(key)
                
        # Fallback to the original single key if numbered keys aren't used
        if not self.pool:
            single_key = os.environ.get("GROQ_API_KEY")
            if single_key:
                self.pool.append(single_key)
                
        if not self.pool:
            logging.error("CRITICAL: No API keys found in environment variables.")
            raise ValueError("Production environment requires at least one valid GROQ_API_KEY.")
            
        # Start with a random key from the pool to distribute the load evenly
        self.current_key = random.choice(self.pool)

    def _rotate_key(self):
        """Removes the exhausted key from the pool and selects a new one."""
        if self.current_key in self.pool:
            self.pool.remove(self.current_key)
            
        if self.pool:
            self.current_key = random.choice(self.pool)
            logging.warning(f"Rate limit hit. Rotated to a new API Key. {len(self.pool)} keys remaining in pool.")
        else:
            logging.error("All API keys in the rotation pool have been exhausted.")
            raise RuntimeError("High traffic alert: The system is currently at maximum capacity. Please try again in 15 minutes.")

    def analyze_cv_against_job(self, cv_text: str, job_desc: str) -> dict:
        """
        Executes parallel evaluation with an automatic retry and fallback mechanism.
        """
        system_prompt = """
        You are an elite Enterprise ATS Analyzer, a Senior Career Coach, and an Executive Copywriter.
        Your task is to deeply analyze the candidate's CV against the target Job Description and output ONLY a valid JSON object.
        YOU MUST BE STRICTLY DETERMINISTIC. For the exact same CV and Job Description, ALWAYS yield the exact same match score and keywords.
        
        CRITICAL INSTRUCTIONS FOR EACH MODULE:
        1. match_score: Calculate a strict, realistic match percentage (0-100). Be deterministic based on strict keyword matching and experience years.
        2. overall_summary: Write a highly accurate, professional paragraph (3-4 sentences) assessing the fit.
        3. matching_keywords: List exact skills present in BOTH the CV and Job Description.
        4. missing_keywords: List critical skills required by the job but missing from the CV. Return as a list of dictionaries [{"skill": "str", "platform": "str"}]. Suggest the BEST professional platform (e.g., Coursera, AWS, HubSpot, Udemy).
        5. ats_improvements: Provide 3 highly actionable, specific tips to modify the CV to pass ATS filters.
        6. bullet_improvements: Select 2-3 weak achievements and rewrite them using the STAR method with quantifiable metrics.
        7. reverse_job_recommendations: IGNORE the target job description for this step. Based SOLELY on the candidate's CV, degree, and real skills, suggest 5 to 6 accurate, highly searchable job titles they are truly qualified to apply for right now.
        8. cover_letter_draft: Write a premium, 4-paragraph Cover Letter (Harvard Business Style).
                - STRICTLY write in the first person ("I", "my", "me"). NEVER use the candidate's name in the body paragraphs.
                - STRICTLY separate EVERY paragraph with double newlines (\\n\\n). Do NOT merge them into a single block of text.
                - Paragraph 1: State the exact position and express genuine professional interest.
                - Paragraph 2: Highlight specific technical skills and map them directly to the job's core requirements.
                - Paragraph 3: Discuss soft skills, problem-solving, and adaptability. Mention proficiency in English and Arabic.
                - Paragraph 4: Strong, professional call to action for an interview.
                - CRITICAL FORMATTING: Start directly with "Dear Hiring Manager,".
                - The sign-off MUST be exactly formatted like this:
                    [End of last paragraph]
                    \\n\\n
                    Sincerely,
                    \\n
                    Nawaf Marwan Almekhlafi
                - Do NOT include any placeholders like [Company Name] or [Date]..
        
        OUTPUT SCHEMA (Strict JSON Format):
        {
            "match_score": int,
            "overall_summary": "str",
            "matching_keywords": ["str"],
            "missing_keywords": [{"skill": "str", "platform": "str"}],
            "ats_improvements": ["str"],
            "bullet_improvements": ["str"],
            "reverse_job_recommendations": ["str"],
            "cover_letter_draft": "str"
        }
        """

        user_prompt = f"""
        --- CANDIDATE CV TEXT ---
        {cv_text}
        
        --- TARGET JOB DESCRIPTION ---
        {job_desc}
        """

        max_attempts = len(self.pool) + 1 # Try as many times as we have keys
        
        for attempt in range(max_attempts):
            try:
                logging.info(f"Attempting API call (Attempt {attempt + 1})...")
                client = OpenAI(
                    api_key=self.current_key,
                    base_url="https://api.groq.com/openai/v1"
                )
                
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.0 
                )
                
                raw_response = response.choices[0].message.content
                result_json = json.loads(raw_response)
                return result_json
                
            except Exception as e:
                error_message = str(e).lower()
                # If we hit a Rate Limit (429), trigger the rotation protocol
                if "429" in error_message or "rate limit" in error_message:
                    if self.pool:
                        self._rotate_key()
                        continue # Retry the loop with the new key
                    else:
                        raise RuntimeError("High traffic alert: The system is currently at maximum capacity. Please try again later.")
                else:
                    # If it's a different error (like JSON parsing), fail normally
                    logging.error(f"Non-Rate-Limit Error encountered: {e}")
                    raise e
                    
        raise RuntimeError("System error: Unable to complete the request after multiple attempts.")