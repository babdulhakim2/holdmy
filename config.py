import os
from dotenv import load_dotenv
from pathlib import Path

class Config:
    # Load environment variables from .env file
    load_dotenv()
    
    # Twilio credentials
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', 'NOT_SET')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', 'NOT_SET')
    TWILIO_NUMBER = os.environ.get('TWILIO_NUMBER', 'NOT_SET')
    
    # Other configuration
    FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    HOLD_MUSIC_URL = os.environ.get('HOLD_MUSIC_URL', 'http://com.twilio.music.classical.s3.amazonaws.com/ith_brahms-116-4.mp3')
    WEBHOOK_BASE_URL = os.environ.get('WEBHOOK_BASE_URL', '').rstrip('/')
    
    # If True, skip Twilio request validation in development
    SKIP_TWILIO_VALIDATION = os.environ.get('SKIP_TWILIO_VALIDATION', 'False').lower() == 'true'
    
    @classmethod
    def validate_config(cls):
        """Validate that all required configuration variables are set."""
        required_vars = [
            'TWILIO_ACCOUNT_SID', 
            'TWILIO_AUTH_TOKEN', 
            'TWILIO_NUMBER',
            'WEBHOOK_BASE_URL'
        ]
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

class DevelopmentConfig(Config):
    FLASK_DEBUG = True
    # Add other development-specific settings

class ProductionConfig(Config):
    FLASK_DEBUG = False
    # Add other production-specific settings

class TestingConfig(Config):
    TESTING = True
    # Add test-specific settings