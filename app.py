# run.py
import os
from app import create_app, db
from app.models import Episode, SharedData

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Episode': Episode, 'SharedData': SharedData}

if __name__ == '__main__':
    app.run(ssl_context='adhoc')