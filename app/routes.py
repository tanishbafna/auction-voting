from flask import Blueprint, request, jsonify
from .models import User, Vote, Option
from . import db, login_manager

main = Blueprint('main', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@main.route('/login', methods=['POST'])
def login():
    # Add login logic here
    pass

@main.route('/vote', methods=['POST'])
def vote():
    # Voting logic here
    pass

@main.route('/suggest', methods=['POST'])
def suggest():
    # Suggestion logic here
    pass