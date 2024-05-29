from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

#-------------------
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    date_created = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

    rooms = db.relationship('Room', backref='creator', lazy=True)
    votes = db.relationship('Vote', backref='voter', lazy=True)
    options = db.relationship('Option', backref='suggester', lazy=True)
    room_participations = db.relationship('RoomParticipant', backref='participant', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Room(db.Model):
    __tablename__ = 'rooms'
    id = db.Column(db.Integer, primary_key=True)
    room_code = db.Column(db.String(6), unique=True, nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    number_of_players = db.Column(db.Integer, nullable=False)
    starting_points = db.Column(db.Integer, nullable=False, default=100)
    deduction_points_per_option = db.Column(db.Integer, nullable=False, default=25)
    status = db.Column(db.Boolean,  nullable=False, default=True)

    options = db.relationship('Option', backref='room', lazy=True)
    participants = db.relationship('RoomParticipant', backref='room', lazy=True)

class Option(db.Model):
    __tablename__ = 'options'
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    suggested_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    option_text = db.Column(db.String(200), nullable=False)
    total_points = db.Column(db.Integer, default=0, nullable=False)

    votes = db.relationship('Vote', backref='option', lazy=True)

class Vote(db.Model):
    __tablename__ = 'votes'
    id = db.Column(db.Integer, primary_key=True)
    option_id = db.Column(db.Integer, db.ForeignKey('options.id'), nullable=False)
    voter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    points_allocated = db.Column(db.Integer, nullable=False, default=0)

class RoomParticipant(db.Model):
    __tablename__ = 'room_participants'
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    is_room_admin = db.Column(db.Boolean, nullable=False, default=False)