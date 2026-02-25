# automation-auditor/src/config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def init_tracing():
    """
    Ensures LangSmith tracing is enabled based on environment variables.
    """
    tracing_enabled = os.environ.get("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    
    if tracing_enabled:
        print(f"--- LangSmith Tracing Enabled: Project='{os.environ.get('LANGCHAIN_PROJECT', 'default')}' ---")
    else:
        print("--- LangSmith Tracing Disabled ---")

# Individual config values can be accessed here
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY") # Added for Gemini support if needed
