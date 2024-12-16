from flask import Flask, request, jsonify
from models import db, Album, Review
from config import Config
from fetchalbums import (
    search_album_by_title_and_artist,
    extract_release_numbers,
    fetch_image_url_by_getting_discogs_id,
    generate_track_dict,
    d,
    get_release_year
)
"""ill need flask-migrate as it works seemlessy with flask-sqlalchemy (its alembic)"""
app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

# Initialize the database tables // should only be used during developement or testing, in production migrations
##flask-migrate are typically used to manage database schemas
with app.app_context():
    db.create_all()

# Routes for albums
"""this only does order by rating in the params so later there will be ordered by date included"""
@app.route('/api/albums', methods=['GET'])
def get_albums():
    order_by = request.args.get('orderBy', 'rating')
    if order_by not in ['rating', 'release_date']:
        return jsonify({"error": "Invalid orderBy parameter"}), 400

    if order_by == 'rating':
        albums = Album.query.join(Review, Review.album_id == Album.id) \
            .add_columns(Album.id, Album.title, Album.artist, Album.release_date, db.func.avg(Review.rating).label("avg_rating")) \
            .group_by(Album.id).order_by(db.desc("avg_rating")).all()
    else:  # order_by == 'release_date'
        albums = Album.query.order_by(Album.release_date.desc()).all()

    return jsonify([album.to_dict() for album in albums])


"""The rating-based query looks good, but be aware that if an album has no reviews, it won't appear in the results due to the join(). You might want to use outerjoin() if you want to include albums without reviews.

Error Handling:
Your error handling is basic but functional. Consider adding more detailed error responses and potential exception handling."""


@app.route('/api/albums/<int:album_id>', methods=['GET'])
def get_album_by_id(album_id):
    album = Album.query.get(album_id)
    if not album:
        return jsonify({"error": "Album not found"}), 404
    return jsonify(album.to_dict())

# Routes for reviews
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
        #release = d.release(release_id)
        #release_year = get_release_year(release_id)

        # Extract details
        album_cover = fetch_image_url_by_getting_discogs_id(release_id)
        release_date = get_release_year(release_id) or None #makes sure that release date is none when none therey


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

####i need release date and i need to input for models a tracklist to the album


if __name__ == '__main__':
    app.run(debug=True)
