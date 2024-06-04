from flask import Blueprint, render_template, flash, redirect, session, request, url_for
from flask_login import login_user, current_user, logout_user, login_required
from flask_request_validator import FORM, GET, Param, validate_params, ValidRequest

from sqlalchemy import func
from sqlalchemy.sql import exists

from .models import db, User, Room, Option, Vote, RoomParticipant
from . import login_manager
from .decorators import admin_required, is_participant, was_participant
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
    if current_user.is_authenticated:
        return redirect(url_for('main.rooms'))
    else:
        return render_template('index.html', user=current_user)

#-----

@main.route('/signUp', methods=['POST'])
@validate_params(
    Param('name', FORM, str, required=True),
    Param('new-username', FORM, str, required=True),
    Param('new-password', FORM, str, required=True),
    Param('confirm-password', FORM, str, required=True),
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
        flash('Invalid admin passcode :(', 'error')
        return redirect(url_for('main.index'))

    # Check for existing username in the database
    if User.query.filter_by(username=form['new-username']).first():
        flash('Username already exists :(', 'error')
        return redirect(url_for('main.index'))
    
    # Check if password is at least 6 characters long
    if len(form['new-password']) < 6:
        flash('Password must be at least 6 characters long :(', 'error')
        return redirect(url_for('main.index'))
    
    # Check if the password and confirm password match
    if form['new-password'] != form['confirm-password']:
        flash('Passwords do not match :(', 'error')
        return redirect(url_for('main.index'))

    # Define roles based on passcodes
    is_admin = form['coAdminPasscode'] == CO_ADMIN_PASSCODE if form['coAdminPasscode'] else False

    # Create new user with hashed password
    new_user = User(
        name=form['name'],
        username=form['new-username'],
        password_hash=generate_password_hash(form['new-password']),
        is_admin=is_admin,
    )

    # Add the new user to the database
    db.session.add(new_user)
    try:
        db.session.commit()
        flash('User successfully created!', 'success')
        return redirect(url_for('main.index'))
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while creating the user :(', 'error')
        return redirect(url_for('main.index'))

#-----

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
        flash('Invalid username or password :(', 'error')
        return redirect(url_for('main.index'))

    # Log the user in
    login_user(user)
    flash('Logged in successfully!', 'success')
    return redirect(url_for('main.rooms'))

#-----

@main.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('main.index'))

#-----

@main.route('/account', methods=['GET'])
@login_required
def account():
    return render_template('account.html', user=current_user)

#-----

@main.route('/account/changePW', methods=['POST'])
@login_required
@validate_params(
    Param('old-password', FORM, str, required=True),
    Param('new-password', FORM, str, required=True),
    Param('confirm-password', FORM, str, required=True)
)
def changePW(valid: ValidRequest):

    # Get the parameters from the request
    form = valid.get_form()

    # Check if the old password is correct
    if not current_user.check_password(form['old-password']):
        flash('Incorrect old password :(', 'error')
        return redirect(url_for('main.account'))
    
    # Check if the new password is at least 6 characters long
    if len(form['new-password']) < 6:
        flash('New password must be at least 6 characters long :(', 'error')
        return redirect(url_for('main.account'))
    
    # Check if the new password matches the confirm password
    if form['new-password'] != form['confirm-password']:
        flash('New password does not match confirm password :(', 'error')
        return redirect(url_for('main.account'))
    
    # Update the user's password
    current_user.password_hash = generate_password_hash(form['new-password'])

    # Commit the changes
    try:
        db.session.commit()
        flash('Password successfully changed!', 'success')
        return redirect(url_for('main.account'))
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while changing the password :(', 'error')
        return redirect(url_for('main.account'))

#-------------------

@main.route('/rooms', methods=['GET'])
@login_required
@validate_params(
    Param('page', GET, int, required=False, default=1)
)
def rooms(valid: ValidRequest):

    # Check if the page number is valid
    try:
        params = valid.get_params()
        current_page = max(1, params.get('page', 1))
        
        total_rooms = db.session.query(Room).count()
        total_pages = max(1, (total_rooms + 9) // 10)
        assert current_page <= total_pages

    except Exception as e:
        flash('Invalid page number :(', 'error')
        return redirect(url_for('main.rooms', page=1))
    
    # Pages to show
    start_page = max(1, current_page - 1)
    end_page = min(total_pages, current_page + 1)
    pages_to_show = list(range(start_page, end_page + 1))

    # Get list of rooms with the creator's name (pagination)
    roomList = db.session.query(
        Room.room_code,
        User.username.label('creator_name'),
        Room.date_created,
        Room.number_of_players,
        Room.status,
        exists().where(
            db.and_(
                RoomParticipant.room_id == Room.id,
                RoomParticipant.user_id == current_user.id
            )
        ).label('is_participant')
    ).join(User, Room.creator_id == User.id).order_by(Room.date_created.desc()).limit(10).offset((current_page - 1) * 10).all()
        
    return render_template('rooms.html', user=current_user, roomList=roomList, pages_to_show=pages_to_show, current_page=current_page, total_pages=total_pages)

#-----

@main.route('/rooms/create', methods=['POST'])
@login_required
@admin_required
@validate_params(
    Param('number_of_players', FORM, int, required=True),
    Param('starting_points', FORM, int, required=False, default=100),
    Param('deduction_points_per_option', FORM, int, required=False, default=25),
    Param('blind', FORM, bool, required=False, default=True)
)
def createRoom(valid: ValidRequest):

    # Get the parameters from the request
    form = valid.get_form()

    # Check if the number of players is valid
    if form['number_of_players'] < 3 or form['number_of_players'] > 20:
        flash('Number of players must be between 3 and 20 :(', 'error')
        return redirect(url_for('main.rooms'))
    
    # Ensure that the starting points are greater than the deduction points per option
    if form['starting_points'] < form['deduction_points_per_option']:
        flash('Starting points must be greater than the deduction points per option :(', 'error')
        return redirect(url_for('main.rooms'))

    # Create a new room
    new_room = Room(
        creator_id=current_user.id,
        room_code=generate_room_code(6),
        number_of_players=form['number_of_players'],
        starting_points=form['starting_points'],
        deduction_points_per_option=form['deduction_points_per_option'],
        blind=form['blind']
    )

    # Add the new room to the database
    db.session.add(new_room)
    try:
        db.session.commit()
        # Get the new room's id
        new_room_id = db.session.query(Room.id).filter_by(room_code=new_room.room_code).first()[0]
        flash('Room successfully created!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while creating the room :(', 'error')
        return redirect(url_for('main.rooms'))
    
    # Add the user to the room
    new_participant = RoomParticipant(
        room_id=new_room_id,
        user_id=current_user.id,
        is_room_admin=True,
        points=form['starting_points']
    )

    # Add the new participant to the database
    db.session.add(new_participant)
    try:
        db.session.commit()
        flash(f'Joined room {new_room.room_code}!', 'success')
        flash('You are the room admin!', 'info')
        return redirect(url_for('main.options', room_code=new_room.room_code))
    except Exception as e:#???
        db.session.rollback()
        flash(f'Couldn\'t join room {new_room.room_code} :(', 'error')
        return redirect(url_for('main.rooms'))

#-----

@main.route('/rooms/<room_code>', methods=['GET'])
@login_required
def room(room_code):

    # Check if the room exists and is active
    room_exists = db.session.query(Room).filter_by(room_code=room_code, status=True).first()
    if not room_exists:
        flash('Room not found :(', 'error')
        return redirect(url_for('main.rooms'))
    
    # Add the user to the room if not already present
    current_participants = db.session.query(RoomParticipant).filter_by(room_id=room_exists.id).all()
    if not any(participant.user_id == current_user.id for participant in current_participants):

        # Check if the room is full
        total_participants = len(current_participants)
        if total_participants >= room_exists.number_of_players:
            flash(f'Room {room_code} is full :(', 'error')
            return redirect(url_for('main.rooms'))
        
        # Add the user to the room
        new_participant = RoomParticipant(
            room_id=room_exists.id,
            user_id=current_user.id,
            is_room_admin=True if room_exists.creator_id == current_user.id else False,
            points=room_exists.starting_points
        )

        # Add the new participant to the database
        db.session.add(new_participant)
        try:
            db.session.commit()
            flash(f'Joined room {room_code}!', 'success')
            flash('You are the room admin!', 'info') if room_exists.creator_id == current_user.id else None
            return redirect(url_for('main.options', room_code=room_code))
        except Exception as e:
            db.session.rollback()
            flash(f'Couldn\'t join room {room_code} :(', 'error')
            return redirect(url_for('main.rooms'))
    
    else:
        return redirect(url_for('main.options', room_code=room_code))

#-----

@main.route('/rooms/<room_code>/options', methods=['GET'])
@login_required
@is_participant
def options(room_code, room):

    # Check if options have already been submitted
    options_submitted = db.session.query(Option).filter_by(room_id=room.id, suggested_by=current_user.id).first()
    if options_submitted:
        return redirect(url_for('main.waitingRoom', room_code=room_code))

    # Set number of option boxes to display
    num_option_boxes = room.starting_points // room.deduction_points_per_option
    return render_template('options.html', user=current_user, room=room, num_option_boxes=num_option_boxes)

#-----

@main.route('/rooms/<room_code>/submitOptions', methods=['POST'])
@login_required
@is_participant
@validate_params(
    Param('option1_text', FORM, str, required=True),
    Param('option2_text', FORM, str, required=False),
    Param('option3_text', FORM, str, required=False)
)
def addOption(valid: ValidRequest, room_code, room):
    
    # Get the parameters from the request
    form = valid.get_form()

    # Remove empty options
    options = [form[f'option{i}_text'] for i in range(1, 4) if form.get(f'option{i}_text', None) and form[f'option{i}_text'].strip() != '']

    # Ensure that the number of options - 1 x deduction points is less than the starting points
    if (len(options) - 1) * room.deduction_points_per_option > room.starting_points:
        flash('Too many options specified :(', 'error')
        return redirect(url_for('main.options', room_code=room_code))

    # Create new options
    for option in options:
        new_option = Option(
            room_id=room.id,
            suggested_by=current_user.id,
            option_text=option
        )

        # Add the new option to the database
        db.session.add(new_option)

    # Update the user's points
    current_participant = db.session.query(RoomParticipant).filter_by(room_id=room.id, user_id=current_user.id).first()
    current_participant.points = max(0, current_participant.points - ((len(options) - 1) * room.deduction_points_per_option))

    # Commit the changes
    try:
        db.session.commit()
        flash('Option(s) successfully added!', 'success')
        return redirect(url_for('main.waitingRoom', room_code=room_code))
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while adding the options :(', 'error')
        return redirect(url_for('main.options', room_code=room_code))

#-----

@main.route('/rooms/<room_code>/waitingRoom', methods=['GET'])
@login_required
@is_participant
def waitingRoom(room_code, room):

    # Count unique number of participants who have submitted options
    options_submitted = db.session.query(func.count(Option.suggested_by.distinct())).filter_by(room_id=room.id).scalar()
    if options_submitted < room.number_of_players:
        return render_template('waiting.html', user=current_user, room=room, participants_left=room.number_of_players - options_submitted, waitType='options')
    else:
        return redirect(url_for('main.voting', room_code=room_code))

#-----

@main.route('/rooms/<room_code>/voting', methods=['GET'])
@login_required
@is_participant
def voting(room_code, room):

    # Redirect if all participants have not submitted options yet
    options_submitted = db.session.query(func.count(Option.suggested_by.distinct())).filter_by(room_id=room.id).scalar()
    if options_submitted < room.number_of_players:
        flash('All participants have not submitted options yet :(', 'error')
        return redirect(url_for('main.waitingRoom', room_code=room_code))

    # Check if the user has already voted
    votes_submitted = db.session.query(Vote).filter_by(room_id=room.id, voter_id=current_user.id).first()
    if votes_submitted:
        return redirect(url_for('main.waitingResults', room_code=room_code))

    # Get the options to vote on
    options = db.session.query(Option).filter_by(room_id=room.id).order_by(Option.option_text).all()

    # Separate the user's own options from the rest
    own_options = []
    other_options = []
    for option in options:
        if option.suggested_by == current_user.id:
            own_options.append(option)
        else:
            other_options.append(option)
    
    # Get the user's current points
    current_participant = db.session.query(RoomParticipant).filter_by(room_id=room.id, user_id=current_user.id).first()

    # Placeholder for the user's self votes
    default_self_points = int(current_participant.points / 2 // len(own_options))
    default_current_points = int(current_participant.points - (default_self_points * len(own_options)))

    return render_template(
        'voting.html',
        user=current_user,
        participant=current_participant,
        room=room,
        own_options=own_options,
        other_options=other_options,
        default_self_points=default_self_points,
        default_current_points=default_current_points,
        len_own_options=len(own_options)
    )

#-----

@main.route('/rooms/<room_code>/submitVotes', methods=['POST'])
@login_required
@is_participant
def submitVotes(room_code, room):

    # Retreive all form data
    form = request.form

    # Create mapping from option ID to points allocated
    votes = {}
    for option_key, points in form.items():
        if option_key.startswith('option'):
            try:
                option_id = int(option_key.split('_')[1])
                votes[option_id] = int(points)
                assert votes[option_id] >= 0
            except Exception as e:
                flash('Invalid vote :(', 'error')
                return redirect(url_for('main.voting', room_code=room_code))
    
    # Get the options to vote on
    options = db.session.query(Option).filter_by(room_id=room.id).all()
    optionIds = [option.id for option in options]
    
    # Remove any votes for options that do not exist
    votes = {option_id: points for option_id, points in votes.items() if option_id in optionIds}

    # Current participant object
    current_participant = db.session.query(RoomParticipant).filter_by(room_id=room.id, user_id=current_user.id).first()

    # Ensure that the total points allocated is less than the user's current points
    if sum(votes.values()) > current_participant.points:
        flash('Total points allocated exceeds your current points :(', 'error')
        return redirect(url_for('main.voting', room_code=room_code))
    
    # Ensure that the user has not voted on their own options with more than 50% of their points
    self_points = 0
    for option in options:
        if option.suggested_by == current_user.id:
            self_points += votes.get(option.id, 0)
    
    if self_points > current_participant.points // 2:
        flash('You cannot allocate more than 50% of your points to your own options :(', 'error')
        return redirect(url_for('main.voting', room_code=room_code))
    
    # Create new votes
    for option in options:
        new_vote = Vote(
            option_id=option.id,
            room_id=room.id,
            voter_id=current_user.id,
            points_allocated=votes.get(option.id, 0)
        )

        # Add the new vote to the database
        db.session.add(new_vote)

    # Update the user's points
    current_participant.points -= sum(votes.values())

    # Add the vote points to the options
    for option_id, points in votes.items():
        option = db.session.query(Option).filter_by(id=option_id).with_for_update().one()
        option.total_points += points

    # Commit the changes
    try:
        db.session.commit()
        flash('Votes successfully submitted!', 'success')
        return redirect(url_for('main.waitingResults', room_code=room_code))
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while submitting the votes :(', 'error')
        return redirect(url_for('main.voting', room_code=room_code))
    
#-----

@main.route('/rooms/<room_code>/waitingResults', methods=['GET'])
@login_required
@is_participant
def waitingResults(room_code, room):
    
    # Count unique number of participants who have submitted votes
    votes_submitted = db.session.query(func.count(Vote.voter_id.distinct())).filter_by(room_id=room.id).scalar()
    if votes_submitted < room.number_of_players:
        return render_template('waiting.html', user=current_user, room=room, participants_left=room.number_of_players - votes_submitted, waitType='votes')
    else:
        return redirect(url_for('main.results', room_code=room_code))
    
#-----

@main.route('/rooms/<room_code>/results', methods=['GET'])
@login_required
@is_participant
def results(room_code, room):

    # Redirect if all participants have not submitted votes yet
    votes_submitted = db.session.query(func.count(Vote.voter_id.distinct())).filter_by(room_id=room.id).scalar()
    if votes_submitted < room.number_of_players:
        flash('All participants have not submitted votes yet :(', 'error')
        return redirect(url_for('main.waitingResults', room_code=room_code))
    
    # Get the options
    resultList = db.session.query(
        Option.option_text,
        Option.total_points,
        Option.suggested_by,
        User.username.label('suggested_by_name')
    ).join(User, Option.suggested_by == User.id).filter(Option.room_id == room.id).order_by(Option.total_points.desc()).all()

    # Add winner option to the room if not already present
    room = db.session.query(Room).filter_by(room_code=room_code).with_for_update().one()
    if not room.result_announced:
        room.result_announced = True
        room.winner_option = max(resultList, key=lambda option: option.total_points).option_text
        
        try:
            db.session.commit()
            flash('Results are in!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while announcing the results :(', 'error')
            return redirect(url_for('main.results', room_code=room_code))

    return render_template('results.html', user=current_user, room=room, resultList=resultList)

#-----

@main.route('/rooms/<room_code>/close', methods=['POST'])
@login_required
@admin_required
@is_participant
def closeRoom(room_code, room):

    # Ensure that user is the room admin
    if room.creator_id != current_user.id:
        flash('You are not the room admin :(', 'error')
        return redirect(url_for('main.results', room_code=room_code))
    
    # Close the room
    room = db.session.query(Room).filter_by(room_code=room_code).with_for_update().one()
    room.status = False
    
    # Delete all room votes
    db.session.query(Vote).filter_by(room_id=room.id).delete()
    
    try:
        db.session.commit()
        flash('Room successfully closed!', 'success')
        return redirect(url_for('main.rooms'))
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while closing the room :(', 'error')
        return redirect(url_for('main.results', room_code=room_code))
    
#-----

@main.route('/rooms/<room_code>/closed/results', methods=['GET'])
@login_required
@was_participant
def closedResults(room_code, room):
    
    # Get the options
    resultList = db.session.query(
        Option.option_text,
        Option.total_points,
        Option.suggested_by,
        User.username.label('suggested_by_name')
    ).join(User, Option.suggested_by == User.id).filter(Option.room_id == room.id).order_by(Option.total_points.desc()).all()

    return render_template('resultsClosed.html', user=current_user, room=room, resultList=resultList)
