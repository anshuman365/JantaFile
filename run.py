# run.py
import os
from dotenv import load_dotenv # Import load_dotenv
from config import DevelopmentConfig, ProductionConfig, TestingConfig, Config # Import all config classes

# Load environment variables from .env file at the very beginning
load_dotenv()

from app import create_app, db
from app.models import Episode, SharedData
# from flask_migrate import Migrate # Uncomment if you are using Flask-Migrate

# Determine which configuration class to use based on FLASK_ENV
env = os.getenv('FLASK_ENV', 'development') # Default to 'development'

if env == 'production':
    config_class = ProductionConfig
elif env == 'testing':
    config_class = TestingConfig
else: # Default to development or if FLASK_ENV is not recognized
    config_class = DevelopmentConfig

app = create_app(config_class) # Pass the selected config class object

# If you are using Flask-Migrate, uncomment the following line:
# migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Episode': Episode, 'SharedData': SharedData}

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')


