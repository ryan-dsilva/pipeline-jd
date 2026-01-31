import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    POCKETBASE_URL: str = os.getenv("POCKETBASE_URL", "http://127.0.0.1:8090")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")


settings = Settings()
