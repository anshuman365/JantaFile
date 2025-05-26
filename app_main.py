# run.py
import os
import threading
import time
import requests
from dotenv import load_dotenv
from config import DevelopmentConfig, ProductionConfig, TestingConfig

# Load environment variables from .env file
load_dotenv()

from app import create_app, db
from app.models import Episode, SharedData

# Determine configuration
env = os.getenv('FLASK_ENV', 'development')
config_class = {
    'production': ProductionConfig,
    'testing': TestingConfig
}.get(env, DevelopmentConfig)

app = create_app(config_class)

# Self-pinging configuration
PING_INTERVAL = 300  # 5 minutes
APP_URL = os.getenv('APP_URL', 'https://jantafile-youtube-care-support.onrender.com')

def wake_up():
    while True:
        try:
            print("Sending self-ping to keep alive")
            requests.get(f"{APP_URL}/health")
        except Exception as e:
            print(f"Ping failed: {str(e)}")
        time.sleep(PING_INTERVAL)

def run_scheduler():
    time.sleep(10)  # Initial delay to let app start
    wake_up()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Episode': Episode, 'SharedData': SharedData}

# Start background thread when running in production
if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()

# Ensure the instance directory exists
#instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
#if not os.path.exists(instance_path):
#    os.makedirs(instance_path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)