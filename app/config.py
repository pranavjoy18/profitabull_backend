import os
from dotenv import load_dotenv

load_dotenv(override=True)

class AppConfig:
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")
