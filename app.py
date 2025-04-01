from flask import Flask, request, jsonify
from flask_cors import CORS
from models import db, Album, Review
from config import Config
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
CORS(app)

db.init_app(app)

# Initialize the database tables
with app.app_context():
    db.create_all()

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
        result.sort(key=lambda x: (x['average_rating'] is None, -1 if x['average_rating'] is None else -x['average_rating']))
    else:  # order_by == 'release_date'
        # Sort by release_date (None values last)
        result.sort(key=lambda x: (x['release_date'] is None, '' if x['release_date'] is None else x['release_date']), reverse=True)
        
    return jsonify(result)

@app.route('/api/albums/<int:album_id>', methods=['GET'])
def get_album_by_id(album_id):
    album = Album.query.get(album_id)
    if not album:
        return jsonify({"error": "Album not found"}), 404
    return jsonify(album.to_dict())

@app.route('/api/reviews', methods=['POST'])
def create_review():
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

    review = Review(title=title, body=body, rating=rating, album_id=album_id)
    db.session.add(review)
    db.session.commit()

    return jsonify(review.to_dict()), 201

@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    return jsonify([review.to_dict() for review in reviews])

@app.route('/api/albums', methods=['POST'])
def add_album():
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
            album_cover=album_cover
        )
        db.session.add(album)
        db.session.commit()

        return jsonify(album.to_dict()), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
