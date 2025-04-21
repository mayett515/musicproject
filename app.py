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

# ✅ Allow CORS from everywhere (no credentials)
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=False)

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

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists"}), 409

    new_user = User(username=username, email=email)
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

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

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

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


@app.route('/api/albums', methods=['GET'])
def get_albums():
    order_by = request.args.get('orderBy', 'rating')
    if order_by not in ['rating', 'release_date']:
        return jsonify({"error": "Invalid orderBy parameter"}), 400

    all_albums = Album.query.all()
    result = []

    for album in all_albums:
        album_dict = album.to_dict()
        reviews = Review.query.filter_by(album_id=album.id).all()

        if reviews:
            avg_rating = sum(review.rating for review in reviews) / len(reviews)
            album_dict['average_rating'] = round(avg_rating, 1)
        else:
            album_dict['average_rating'] = None

        result.append(album_dict)

    if order_by == 'rating':
        result.sort(key=lambda x: (x['average_rating'] is None, -1 if x['average_rating'] is None else -x['average_rating']))
    else:
        result.sort(key=lambda x: (x['release_date'] is None, '' if x['release_date'] is None else x['release_date']), reverse=True)

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

    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            return jsonify({"error": "Rating must be between 1 and 5"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Rating must be a number between 1 and 5"}), 400

    album = Album.query.get(album_id)
    if not album:
        return jsonify({"error": "Album not found"}), 404

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

    query = Review.query

    if album_id:
        query = query.filter_by(album_id=album_id)
    if user_id:
        query = query.filter_by(user_id=user_id)

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

    existing_album = Album.query.filter_by(title=title, artist=artist).first()
    if existing_album:
        return jsonify({"error": "Album already exists"}), 409

    try:
        search_results = search_album_by_title_and_artist(title, artist)
        release_id = extract_release_numbers(search_results)

        album_cover = fetch_image_url_by_getting_discogs_id(release_id)
        release_date = get_release_year(release_id) or None

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
