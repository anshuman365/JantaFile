import hashlib
import os
import re
from flask import current_app
from cryptography.fernet import Fernet
from base64 import urlsafe_b64encode, urlsafe_b64decode # Import base64 encoding/decoding functions

class SecurityUtils:
    _cipher = None

    @classmethod
    def _get_cipher(cls):
        """Lazily initialize and return the Fernet cipher."""
        if cls._cipher is None:
            encryption_key = os.getenv('ENCRYPTION_KEY')
            
            # --- DEBUGGING FOR ENCRYPTION_KEY IN _get_cipher ---
            print(f"DEBUG (_get_cipher): Raw ENCRYPTION_KEY from os.getenv: '{encryption_key}'")
            print(f"DEBUG (_get_cipher): Type of ENCRYPTION_KEY: {type(encryption_key)}")
            if encryption_key:
                print(f"DEBUG (_get_cipher): Length of ENCRYPTION_KEY: {len(encryption_key)}")
                print(f"DEBUG (_get_cipher): ENCRYPTION_KEY ends with '=': {encryption_key.endswith('=')}")
                print(f"DEBUG (_get_cipher): ENCRYPTION_KEY contains whitespace: {' ' in encryption_key or '\\n' in encryption_key or '\\r' in encryption_key}")
            # --- END DEBUGGING ---

            if not encryption_key:
                raise ValueError("ENCRYPTION_KEY environment variable is not set.")
            try:
                cls._cipher = Fernet(encryption_key.encode('utf-8'))
            except Exception as e:
                raise ValueError(f"Invalid ENCRYPTION_KEY: {e}. Ensure it's a valid Fernet key.")
        return cls._cipher

    @staticmethod
    def generate_submission_code():
        import secrets
        return secrets.token_urlsafe(16)[:16]

    @staticmethod
    def allowed_file(filename):
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in \
            current_app.config['ALLOWED_EXTENSIONS']

    @staticmethod
    def hash_ip(ip):
        return hashlib.blake2b(
            ip.encode() + os.urandom(16)
        ).hexdigest()
        
    @staticmethod
    def encrypt_symmetric(data_bytes):
        """
        Encrypts bytes data using the Fernet symmetric key.
        The ENCRYPTION_KEY must be set in environment variables.
        """
        if not isinstance(data_bytes, bytes):
            data_bytes = str(data_bytes).encode('utf-8')
        
        cipher = SecurityUtils._get_cipher()
        return cipher.encrypt(data_bytes)

    @staticmethod
    def decrypt_symmetric(encrypted_data_bytes):
        """
        Decrypts bytes data using the Fernet symmetric key.
        The ENCRYPTION_KEY must be set in environment variables.
        Returns bytes.
        """
        cipher = SecurityUtils._get_cipher()
        return cipher.decrypt(encrypted_data_bytes)

    @staticmethod
    def bytes_to_base64_string(data_bytes):
        """Converts bytes to a URL-safe base64 encoded string."""
        return urlsafe_b64encode(data_bytes).decode('utf-8')

    @staticmethod
    def base64_string_to_bytes(b64_string):
        """Converts a URL-safe base64 encoded string back to bytes."""
        return urlsafe_b64decode(b64_string.encode('utf-8'))

    @staticmethod
    def sanitize_filename(filename):
        """
        Sanitizes a filename to remove potentially dangerous characters.
        Limits filename length to 255 characters.
        """
        cleaned = re.sub(r'[^a-zA-Z0-9\-_.]', '', filename)
        return cleaned[:255]


