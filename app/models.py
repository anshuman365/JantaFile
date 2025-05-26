# app/models.py
from app import db
from datetime import datetime
from sqlalchemy.dialects.mysql import JSON
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        """Hashes the password and stores it."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks a given password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Episode(db.Model):
    __tablename__ = 'episode'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content_hash = db.Column(db.String(64), unique=True)
    encrypted_docs = db.Column(db.JSON)
    published_at = db.Column(db.DateTime, default=datetime.utcnow)
    tags = db.Column(db.JSON)
    is_verified = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text, nullable=False)
    documents = db.Column(db.JSON)
    youtube_id = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def search(cls, query):
        if query:
            return cls.query.filter(
                cls.title.ilike(f'%{query}%') |
                cls.description.ilike(f'%{query}%')
            ).all()
        return []

    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description
        }

class SharedData(db.Model):
    __tablename__ = 'shared_data'

    id = db.Column(db.Integer, primary_key=True)
    encrypted_payload = db.Column(db.LargeBinary)
    ip_hash = db.Column(db.String(128), nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    title = db.Column(db.String(200))
    description = db.Column(db.Text, nullable=False)
    files = db.Column(db.JSON)
    # NEW: Add contact_method column
    contact_method = db.Column(db.String(50)) # e.g., 'Email', 'Phone', 'Telegram', 'Instagram'
    contact = db.Column(db.Text) # This will store the encrypted contact info
    submission_code = db.Column(db.String(32), unique=True, nullable=False)

# app/models.py (add this class)
class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    endpoint = db.Column(db.Text, unique=True)
    keys = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
