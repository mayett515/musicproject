from flask import Flask, request, jsonify
from flask_cors import CORS
from models import db, Album, Review, User
from config import Config
from auth import token_required, create_token, get_current_user
import os
from fetchalbums import (
    search_album_by_title_and_artist,
    extract_release_numbers,
    fetch_image_url_by_getting_discogs_id,
    generate_track_dict,
    d,
    get_release_year
)

app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS for all routes
CORS(app, supports_credentials=True)

db.init_app(app)

# Initialize the database tables
with app.app_context():
    db.create_all()


# Authentication routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"error": "Username, email, and password are required"}), 400

    # Check if username or email already exists
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists"}), 409

    # Create new user
    new_user = User(username=username, email=email)
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    # Generate JWT token
    token = create_token(new_user.id)

    return jsonify({
        "message": "User registered successfully",
        "token": token,
        "user": new_user.to_dict()
    }), 201


@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    # Find user by email
    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    # Generate JWT token
    token = create_token(user.id)

    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": user.to_dict()
    }), 200


@app.route('/api/auth/user', methods=['GET'])
@token_required
def get_user(current_user):
    return jsonify(current_user.to_dict()), 200


# Routes for albums
@app.route('/api/albums', methods=['GET'])
def get_albums():
    order_by = request.args.get('orderBy', 'rating')
    if order_by not in ['rating', 'release_date']:
        return jsonify({"error": "Invalid orderBy parameter"}), 400

    # Get all albums first
    all_albums = Album.query.all()
    result = []

    # For each album, calculate the average rating from its reviews
    for album in all_albums:
        album_dict = album.to_dict()
        reviews = Review.query.filter_by(album_id=album.id).all()

        if reviews:
            # Calculate the average rating if there are reviews
            avg_rating = sum(review.rating for review in reviews) / len(reviews)
            album_dict['average_rating'] = round(avg_rating, 1)  # Round to 1 decimal place
        else:
            # No reviews yet
            album_dict['average_rating'] = None

        result.append(album_dict)

    # Sort based on the requested order
    if order_by == 'rating':
        # Sort by average_rating (None values last)
        result.sort(
            key=lambda x: (x['average_rating'] is None, -1 if x['average_rating'] is None else -x['average_rating']))
    else:  # order_by == 'release_date'
        # Sort by release_date (None values last)
        result.sort(key=lambda x: (x['release_date'] is None, '' if x['release_date'] is None else x['release_date']),
                    reverse=True)

    return jsonify(result)


@app.route('/api/albums/<int:album_id>', methods=['GET'])
def get_album_by_id(album_id):
    album = Album.query.get(album_id)
    if not album:
        return jsonify({"error": "Album not found"}), 404
    return jsonify(album.to_dict())


@app.route('/api/reviews', methods=['POST'])
@token_required
def create_review(current_user):
    data = request.json
    title = data.get("title")
    body = data.get("body")
    rating = data.get("rating")
    album_id = data.get("album_id")

    if not all([title, body, rating is not None, album_id]):
        return jsonify({"error": "Missing required fields"}), 400

    # Ensure rating is an integer between 1-5
    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            return jsonify({"error": "Rating must be between 1 and 5"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Rating must be a number between 1 and 5"}), 400

    # Check if album exists
    album = Album.query.get(album_id)
    if not album:
        return jsonify({"error": "Album not found"}), 404

    # Check if user already reviewed this album
    existing_review = Review.query.filter_by(user_id=current_user.id, album_id=album_id).first()
    if existing_review:
        return jsonify({"error": "You have already reviewed this album"}), 409

    review = Review(
        title=title,
        body=body,
        rating=rating,
        album_id=album_id,
        user_id=current_user.id
    )
    db.session.add(review)
    db.session.commit()

    return jsonify(review.to_dict()), 201


@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    album_id = request.args.get('album_id')
    user_id = request.args.get('user_id')

    # Base query
    query = Review.query

    # Apply filters if provided
    if album_id:
        query = query.filter_by(album_id=album_id)

    if user_id:
        query = query.filter_by(user_id=user_id)

    # Order by creation date (newest first)
    reviews = query.order_by(Review.created_at.desc()).all()

    return jsonify([review.to_dict() for review in reviews])


@app.route('/api/reviews/<int:review_id>', methods=['GET'])
def get_review_by_id(review_id):
    review = Review.query.get(review_id)
    if not review:
        return jsonify({"error": "Review not found"}), 404
    return jsonify(review.to_dict())


@app.route('/api/albums', methods=['POST'])
@token_required
def add_album(current_user):
    data = request.json
    title = data.get('title')
    artist = data.get('artist')

    if not title or not artist:
        return jsonify({"error": "Title and artist are required"}), 400

    # Check if the album already exists
    existing_album = Album.query.filter_by(title=title, artist=artist).first()
    if existing_album:
        return jsonify({"error": "Album already exists"}), 409

    # Use the Discogs API to search for the album
    try:
        search_results = search_album_by_title_and_artist(title, artist)
        release_id = extract_release_numbers(search_results)

        # Extract details
        album_cover = fetch_image_url_by_getting_discogs_id(release_id)
        release_date = get_release_year(release_id) or None

        # Add to the database
        album = Album(
            title=title,
            artist=artist,
            release_date=release_date,
            album_cover=album_cover,
            added_by=current_user.id
        )
        db.session.add(album)
        db.session.commit()

        return jsonify(album.to_dict()), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))