from . import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    points = db.Column(db.Integer, default=100)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    option_id = db.Column(db.Integer, nullable=False)
    points = db.Column(db.Integer, nullable=False)

class Option(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    suggestion = db.Column(db.String(200), nullable=False)
    total_points = db.Column(db.Integer, default=0)