# run.py
import os
from app import create_app, db
from app.models import Episode, SharedData
import threading
import time
import requests

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Episode': Episode, 'SharedData': SharedData}

# Self-pinging configuration
PING_INTERVAL = 300  # 5 minutes
APP_URL = os.environ.get('APP_URL', 'http://localhost:5000')

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

if __name__ == '__main__':
    # Start background thread when running locally
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        scheduler_thread = threading.Thread(target=run_scheduler)
        scheduler_thread.daemon = True
        scheduler_thread.start()
    app.run(ssl_context='adhoc')

# Start background thread when running on Render
if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()