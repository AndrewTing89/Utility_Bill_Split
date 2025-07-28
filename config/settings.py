import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

class Settings:
    # Base directory
    BASE_DIR = BASE_DIR
    
    # Gmail Configuration
    GMAIL_USER_EMAIL = os.getenv('GMAIL_USER_EMAIL', 'andrewhting@gmail.com')
    GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    CREDENTIALS_PATH = BASE_DIR / 'credentials.json'
    TOKEN_PATH = BASE_DIR / 'token.json'
    
    # Venmo Configuration
    ROOMMATE_VENMO = os.getenv('ROOMMATE_VENMO', 'UshiLo')
    ROOMMATE_PHONE = os.getenv('ROOMMATE_PHONE', '+1234567890')
    MY_VENMO_USERNAME = os.getenv('MY_VENMO_USERNAME', 'andrewhting')
    MY_PHONE = os.getenv('MY_PHONE', '+1234567890')
    
    # Email Configuration
    ROOMMATE_EMAIL = os.getenv('ROOMMATE_EMAIL', 'loushic@gmail.com')
    MY_EMAIL = os.getenv('MY_EMAIL', 'andrewhting@gmail.com')
    EMAIL_METHOD = os.getenv('EMAIL_METHOD', 'mac_mail_app')
    PGE_SENDER = 'DoNotReply@billpay.pge.com'
    
    # Bill Configuration
    ROOMMATE_SPLIT_RATIO = float(os.getenv('ROOMMATE_SPLIT_RATIO', '0.333333'))
    MY_SPLIT_RATIO = float(os.getenv('MY_SPLIT_RATIO', '0.666667'))
    
    # Feature Flags
    ENABLE_AUTO_OPEN = os.getenv('ENABLE_AUTO_OPEN', 'true').lower() == 'true'
    ENABLE_PDF_GENERATION = os.getenv('ENABLE_PDF_GENERATION', 'true').lower() == 'true'
    ENABLE_EMAIL_NOTIFICATIONS = os.getenv('ENABLE_EMAIL_NOTIFICATIONS', 'false').lower() == 'true'
    ENABLE_TEXT_MESSAGING = os.getenv('ENABLE_TEXT_MESSAGING', 'true').lower() == 'true'
    TEST_MODE = os.getenv('TEST_MODE', 'true').lower() == 'true'
    
    # Paths
    DATA_DIR = BASE_DIR / 'data'
    PDF_DIR = DATA_DIR / 'pdfs'
    LOGS_DIR = BASE_DIR / 'logs'
    DB_PATH = DATA_DIR / 'bills.db'
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist"""
        for dir_path in [cls.DATA_DIR, cls.PDF_DIR, cls.LOGS_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)

settings = Settings()