from functools import wraps
from flask import redirect, flash, url_for
from flask_login import current_user
from .models import db, Room, RoomParticipant

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('You do not have permission to create/close rooms :(', 'error')
            return redirect(url_for('main.rooms'))
        return f(*args, **kwargs)
    return decorated_function

def is_participant(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        room_code = kwargs.get('room_code')
        room = db.session.query(Room).filter_by(room_code=room_code, status=True).first()

        if not room:
            flash('Room not found :(', 'error')
            return redirect(url_for('main.rooms'))
        
        check_participant = db.session.query(RoomParticipant).filter_by(room_id=room.id, user_id=current_user.id).first()
        if not check_participant:
            flash('You are not a player in this room :(', 'error')
            return redirect(url_for('main.rooms'))
        
        kwargs['room'] = room
        return f(*args, **kwargs)
    return decorated_function

def was_participant(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        room_code = kwargs.get('room_code')
        room = db.session.query(Room).filter_by(room_code=room_code, status=False, result_announced=True).first()

        if not room:
            flash('Room not found :(', 'error')
            return redirect(url_for('main.rooms'))
        
        check_participant = db.session.query(RoomParticipant).filter_by(room_id=room.id, user_id=current_user.id).first()
        if not check_participant:
            flash('You were not a player in this room :(', 'error')
            return redirect(url_for('main.rooms'))
        
        kwargs['room'] = room
        return f(*args, **kwargs)
    return decorated_function