# from flask_marshmallow import Marshmallow
# from marshmallow import validates, ValidationError
# """flask marshmallow"""
# ma = Marshmallow(app)
#
# class ReviewSchema(ma.SQLAlchemySchema):
#     class Meta:
#         model = Review
#
#     id = ma.auto_field()
#     title = ma.auto_field()
#     body = ma.auto_field()
#     rating = ma.auto_field()
#     album_id = ma.auto_field()
#
#     @validates('rating')
#     def validate_rating(self, value):
#         if value < 0 or value > 5:
#             raise ValidationError('Rating must be between 0 and 5')
#
# review_schema = ReviewSchema()
#
# @app.route('/api/reviews', methods=['POST'])
# def create_review():
#     try:
#         review = review_schema.load(request.json, session=db.session)
#         db.session.add(review)
#         db.session.commit()
#         return jsonify(review.to_dict()), 201
#     except ValidationError as err:
#         return jsonify(err.messages), 400
#
#
#
# """flask sqlalchemy"""
# @app.route('/api/reviews', methods=['POST'])
# def create_review():
#     # Validate data first
#     if not all(request.json.get(field) for field in ['title', 'body', 'rating', 'album_id']):
#         return jsonify({"error": "Missing required fields"}), 400
#
#     try:
#         # Additional validation or processing can be added here
#         review = Review(
#             title=request.json['title'],
#             body=request.json['body'],
#             rating=request.json['rating'],
#             album_id=request.json['album_id']
#         )
#
#         # Use add() and commit in a try-except block
#         db.session.add(review)
#         db.session.commit()
#         return jsonify(review.to_dict()), 201
#     except Exception as e:
#         # Important: rollback the session on error
#         db.session.rollback()
#         return jsonify({"error": "Could not create review", "details": str(e)}), 500
#
#
#

"""only marshmallow"""


# from marshmallow import Schema, fields, ValidationError
#
# class ReviewSchema(Schema):
#     title = fields.Str(required=True)
#     body = fields.Str(required=True)
#     rating = fields.Float(required=True)
#     album_id = fields.Int(required=True)
#
# review_schema = ReviewSchema()
#
# @app.route('/api/reviews', methods=['POST'])
# def create_review():
#     try:
#         # Validate the incoming data
#         data = review_schema.load(request.json)
#     except ValidationError as err:
#         return jsonify(err.messages), 400
#
#     try:
#         review = Review(**data)
#         db.session.add(review)
#         db.session.commit()
#         return jsonify(review.to_dict()), 201
#     except Exception as e:
#         db.session.rollback()
#         return jsonify({"error": str(e)}), 500