import os

class Config:
    API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    SCRAPER_ENDPOINT = ""
    LOCAL_MODE = True  # True = dummy data, False = call API