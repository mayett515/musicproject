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

    if order_by == 'rating':
        albums = Album.query.join(Review, Review.album_id == Album.id) \
            .add_columns(
                Album.id,
                Album.title,
                Album.artist,
                Album.release_date,
                db.func.avg(Review.rating).label("avg_rating")
            ) \
            .group_by(Album.id).order_by(db.desc("avg_rating")).all()

        result = []
        for album in albums:
            album_dict = album[0].to_dict()
            album_dict['average_rating'] = float(album[1]) if album[1] is not None else None
            result.append(album_dict)
        return jsonify(result)
    else:
        albums = Album.query.order_by(Album.release_date.desc()).all()
        return jsonify([album.to_dict() for album in albums])

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

    if not all([title, body, rating, album_id]):
        return jsonify({"error": "Missing required fields"}), 400

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
