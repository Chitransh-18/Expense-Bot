from flask import Flask
import threading
from config import logger, PORT

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_web_server():
    """Run Flask server on configured port for health checks"""
    try:
        app.run(host='0.0.0.0', port=PORT)
    except Exception as e:
        logger.error(f"Error running Flask web server: {e}")

def start_web_server_thread():
    """Start Flask web server in a daemon thread"""
    server_thread = threading.Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()
    logger.info(f"Flask health check server started on port {PORT}")
