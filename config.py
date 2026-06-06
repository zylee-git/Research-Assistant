import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    
    DATA_DIR = "data"
    MEMORY_DIR = os.path.join(DATA_DIR, "memory")
    PAPERS_DIR = os.path.join(DATA_DIR, "papers")
    
    MAX_PAPERS = 10
    MAX_TOKENS = 8192

    @classmethod
    def ensure_dirs(cls):
        for d in [cls.MEMORY_DIR, cls.PAPERS_DIR]:
            os.makedirs(d, exist_ok=True)

Config.ensure_dirs()