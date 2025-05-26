# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager # NEW: Import LoginManager
from config import Config


db = SQLAlchemy()
login_manager = LoginManager() # NEW: Initialize LoginManager

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    from app.routes import limiter

    db.init_app(app)
    limiter.init_app(app)

    # NEW: Initialize Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login' # NEW: Specify the login view for redirection
    login_manager.login_message_category = 'info' # NEW: Category for flash messages

    # NEW: User loader callback for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User # Import here to avoid circular dependency
        return User.query.get(int(user_id))

    with app.app_context():
        db.create_all()

    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    from app.admin_routes import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # NEW: Register the authentication blueprint
    from app.auth_routes import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth') # All auth routes will start with /auth

    return app


