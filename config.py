import os
import secrets


class Config:
    # Base directory of the application
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # Ensure the data folder exists for SQLite
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    os.makedirs(DATA_DIR, exist_ok=True)

    # Database configuration
    # Use PostgreSQL if DATABASE_URL is set, otherwise use SQLite
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

    # Handle PostgreSQL URL format for SQLAlchemy
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)

    # Default to SQLite if no DATABASE_URL is provided
    if not SQLALCHEMY_DATABASE_URI:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(DATA_DIR, 'music_reviews.db')}"

    # SQLAlchemy configuration
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT Secret Key - generate a secure random key if not provided
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

    # Discogs API configuration
    DISCOGS_API_TOKEN = os.environ.get('DISCOGS_API_TOKEN')

    # CORS settings
    CORS_HEADERS = 'Content-Type,Authorization'