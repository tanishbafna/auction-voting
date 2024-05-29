from flask import Blueprint, request, jsonify, render_template, flash, redirect, session
from flask_login import login_user, current_user, logout_user, login_required
from flask_request_validator import PATH, FORM, GET, Param, validate_params, Enum, ValidRequest

from .models import db, User, Room, Option, Vote, RoomParticipant
from . import login_manager
from .decorators import admin_required
from .utils import generate_room_code

import os
from dotenv import load_dotenv; load_dotenv()
from werkzeug.security import generate_password_hash

#-------------------

ADMIN_PASSCODE = os.getenv('ADMIN_PASSCODE')
CO_ADMIN_PASSCODE = os.getenv('CO_ADMIN_PASSCODE')

main = Blueprint('main', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#-------------------

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/signUp', methods=['POST'])
@validate_params(
    Param('name', FORM, str, required=True),
    Param('username', FORM, str, required=True),
    Param('password', FORM, str, required=True),
    Param('adminPasscode', FORM, str, required=True),
    Param('coAdminPasscode', FORM, str, required=False),
)
def signUp(valid: ValidRequest):

    # Get the parameters from the request
    form = valid.get_form()

    # Check if an admin allowed the user to sign up
    try:
        assert form['adminPasscode'] == ADMIN_PASSCODE
    except:
        flash('Invalid admin passcode :(')
        return redirect('/', code=401)

    # Check for existing username in the database
    if User.query.filter_by(username=form['username']).first():
        flash('Username already exists :(')
        return redirect('/', code=409)

    # Define roles based on passcodes
    is_admin = form['coAdminPasscode'] == CO_ADMIN_PASSCODE if form['coAdminPasscode'] else False

    # Create new user with hashed password
    new_user = User(
        name=form['name'],
        username=form['username'],
        password_hash=generate_password_hash(form['password']),
        is_admin=is_admin,
    )

    # Add the new user to the database
    db.session.add(new_user)
    try:
        db.session.commit()
        flash('User successfully created!')
        return redirect('/', code=201)
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while creating the user :(')
        return redirect('/', code=422)

@main.route('/login', methods=['POST'])
@validate_params(
    Param('username', FORM, str, required=True),
    Param('password', FORM, str, required=True)
)
def login(valid: ValidRequest):

    # Get the parameters from the request
    form = valid.get_form()

    # Check if the user exists in the database
    user = User.query.filter_by(username=form['username']).first()

    if not user or not user.check_password(form['password']):
        flash('Invalid username or password :(')
        return redirect('/', code=401)

    # Log the user in
    login_user(user)
    flash('Logged in successfully!')
    return redirect('/rooms', code=200)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('Logged out successfully!')
    return redirect('/', code=200)

#-------------------

@main.route('/rooms', methods=['GET'])
@login_required
def rooms():
    # Get list of active rooms with the creator's name
    roomList = db.session.query(
        Room.room_code,
        User.username.label('creator_name'),
        Room.date_created,
        Room.number_of_players
    ).join(User, Room.creator_id == User.id).filter(Room.status == True).order_by(Room.date_created.desc()).all()
    return render_template('rooms.html', user=current_user, roomList=roomList)

@main.route('/rooms/create', methods=['POST'])
@login_required
@admin_required
@validate_params(
    Param('number_of_players', FORM, int, required=True),
    Param('starting_points', FORM, int, required=False, default=100),
    Param('deduction_points_per_option', FORM, int, required=False, default=25)
)
def createRoom(valid: ValidRequest):

    # Get the parameters from the request
    form = valid.get_form()

    # Create a new room
    new_room = Room(
        creator_id=current_user.id,
        room_code=generate_room_code(6),
        number_of_players=form['number_of_players'],
        starting_points=form['starting_points'],
        deduction_points_per_option=form['deduction_points_per_option']
    )

    # Add the new room to the database
    db.session.add(new_room)
    try:
        db.session.commit()
        # Get the new room's id
        new_room_id = db.session.query(Room.id).filter_by(room_code=new_room.room_code).first()
        flash('Room successfully created!')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while creating the room :(')
        return redirect('/rooms', code=422)
    
    # Add the user to the room
    new_participant = RoomParticipant(
        room_id=new_room_id,
        user_id=current_user.id,
        is_room_admin=True
    )

    # Add the new participant to the database
    db.session.add(new_participant)
    try:
        db.session.commit()
        flash(f'Joined room {new_room.room_code}!')
        flash('You are the room admin!')
        return redirect(f'/rooms/{new_room.room_code}/options', code=201)
    except Exception as e:
        db.session.rollback()
        flash(f'Couldn\'t join room {new_room.room_code} :(')
        return redirect('/rooms', code=500)

@main.route('/rooms/<room_code>', methods=['GET'])
@login_required
def room(room_code):

    # Check if the room exists and is active
    room_exists = db.session.query(Room).filter_by(room_code=room_code, status=True).first()
    if not room_exists:
        flash('Room not found :(')
        return redirect('/rooms', code=404)
    
    # Add the user to the room if not already present
    current_participants = db.session.query(RoomParticipant).filter_by(room_id=room_exists.id).all()
    if not any(participant.user_id == current_user.id for participant in current_participants):

        # Check if the room is full
        total_participants = len(current_participants)
        if total_participants >= room_exists.number_of_players:
            flash(f'Room {room_code} is full :(')
            return redirect('/rooms', code=403)
        
        # Add the user to the room
        new_participant = RoomParticipant(
            room_id=room_exists.id,
            user_id=current_user.id,
            is_room_admin=True if total_participants == 0 else False
        )

        # Add the new participant to the database
        db.session.add(new_participant)
        try:
            db.session.commit()
            flash(f'Joined room {room_code}!')
            flash('You are the room admin!') if total_participants == 0 else None
            return redirect(f'/rooms/{room_code}/options', code=201)
        except Exception as e:
            db.session.rollback()
            flash(f'Couldn\'t join room {room_code} :(')
            return redirect('/rooms', code=500)
    
    else:
        return redirect(f'/rooms/{room_code}/options', code=200)