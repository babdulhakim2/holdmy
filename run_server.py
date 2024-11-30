from app import app
from config import Config

if __name__ == "__main__":
    print("\nStarting Flask server...")
    try:
        app.run(
            host='0.0.0.0',  # Allow external connections
            port=5001,
            debug=Config.FLASK_DEBUG,
            use_reloader=False  # Disable reloader when using with ngrok
        )
    except Exception as e:
        print(f"Error starting server: {e}") 