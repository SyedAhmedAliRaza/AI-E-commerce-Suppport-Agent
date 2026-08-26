import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

class Settings:
    COMPANY_NAME: str = "TechMania"
    BASE_DIR: str = BASE_DIR
    
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    GOOGLE_CREDENTIALS_FILE: str = os.getenv("GOOGLE_CREDENTIALS_FILE", os.path.join(BASE_DIR, "credentials.json"))
    SPREADSHEET_ID: str = os.getenv("SPREADSHEET_ID", "")
    PRODUCTS_SPREADSHEET_ID: str = os.getenv("PRODUCTS_SPREADSHEET_ID", "")
    ORDERS_SPREADSHEET_ID: str = os.getenv("ORDERS_SPREADSHEET_ID", "")
    LOGS_SPREADSHEET_ID: str = os.getenv("LOGS_SPREADSHEET_ID", "")
    
    POLICY_DOCX_PATH: str = os.getenv("POLICY_DOCX_PATH", os.path.join(BASE_DIR, "company_policy.docx"))
    CHROMA_DB_DIR: str = os.getenv("CHROMA_DB_DIR", os.path.join(BASE_DIR, "chroma_db"))
    
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SENDER_EMAIL: str = os.getenv("SENDER_EMAIL", "")
    
    @property
    def has_gemini(self) -> bool:
        return bool(self.GEMINI_API_KEY and len(self.GEMINI_API_KEY.strip()) > 10)

    @property
    def has_google_sheets(self) -> bool:
        has_creds = os.path.exists(self.GOOGLE_CREDENTIALS_FILE)
        has_any_id = bool(self.SPREADSHEET_ID.strip() or self.PRODUCTS_SPREADSHEET_ID.strip() or self.ORDERS_SPREADSHEET_ID.strip())
        return has_creds and has_any_id

    @property
    def has_smtp(self) -> bool:
        return bool(self.SMTP_USER and self.SMTP_PASSWORD)

settings = Settings()
