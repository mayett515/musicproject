import jwt
from functools import wraps
from flask import request, jsonify, current_app
from datetime import datetime, timedelta
from models import User


# JWT token functions
def create_token(user_id):
    """Create a JWT token for the user"""
    payload = {
        'exp': datetime.utcnow() + timedelta(days=1),  # Token expires in 1 day
        'iat': datetime.utcnow(),
        'sub': user_id
    }
    token = jwt.encode(
        payload,
        current_app.config.get('SECRET_KEY'),
        algorithm='HS256'
    )
    return token


def decode_token(token):
    """Decode the JWT token"""
    try:
        payload = jwt.decode(
            token,
            current_app.config.get('SECRET_KEY'),
            algorithms=['HS256']
        )
        return payload['sub']
    except jwt.ExpiredSignatureError:
        return None  # Token has expired
    except jwt.InvalidTokenError:
        return None  # Invalid token


# Auth decorators
def token_required(f):
    """Decorator to require a valid JWT token for a route"""

    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')

        if auth_header:
            # Expected format: "Bearer <token>"
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]

        if not token:
            return jsonify({'error': 'Authentication token is missing!'}), 401

        user_id = decode_token(token)
        if not user_id:
            return jsonify({'error': 'Invalid or expired token!'}), 401

        # Get the user from the database
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found!'}), 404

        # Pass the authenticated user to the route
        return f(user, *args, **kwargs)

    return decorated


def get_current_user():
    """Get the current authenticated user (or None if not authenticated)"""
    token = None
    auth_header = request.headers.get('Authorization')

    if auth_header:
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == 'bearer':
            token = parts[1]

    if not token:
        return None

    user_id = decode_token(token)
    if not user_id:
        return None

    return User.query.get(user_id)