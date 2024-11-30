from config import Config
import os

def test_env_loading():
    print("\nTesting environment variable loading:")
    
    # Print current working directory
    print(f"Current working directory: {os.getcwd()}")
    
    # Try to load config
    try:
        Config.validate_config()
    except Exception as e:
        print(f"Error validating config: {e}")
    
    # Try direct environment variable access
    print("\nDirect environment variable access:")
    print(f"TWILIO_ACCOUNT_SID: {os.environ.get('TWILIO_ACCOUNT_SID', 'NOT_FOUND')}")
    print(f"TWILIO_AUTH_TOKEN: {os.environ.get('TWILIO_AUTH_TOKEN', 'NOT_FOUND')}")
    print(f"TWILIO_NUMBER: {os.environ.get('TWILIO_NUMBER', 'NOT_FOUND')}")

if __name__ == "__main__":
    test_env_loading() 