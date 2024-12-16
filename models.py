from flask_sqlalchemy import SQLAlchemy
import typing
db = SQLAlchemy()

class Album(db.Model): #dbmodel being base class that all ormmodels inherit from
    __tablename__ = "albums"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    artist = db.Column(db.String(255), nullable=False)
    release_date = db.Column(db.String(50), nullable=True)
    album_cover = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "artist": self.artist,
            "release_date": self.release_date,
            "album_cover": self.album_cover,
        }


class Review(db.Model):
    __tablename__ = "reviews"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    album_id = db.Column(db.Integer, db.ForeignKey("albums.id"), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "rating": self.rating,
            "created_at": self.created_at,
            "album_id": self.album_id,
        }
