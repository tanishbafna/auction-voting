from .models import db, User

import random
import string
from werkzeug.security import generate_password_hash

def generate_room_code(N):
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(N))

def populate_db():
    addUsers = [
        {
            'name': 'Tanish Bafna',
            'username': 'tanish',
            'password': 'tanish',
            'is_admin': True,
        },
        {
            'name': 'Niyati Bafna',
            'username': 'niyati',
            'password': 'niyati',
            'is_admin': True,
        },
        {
            'name': 'Mitali Bafna',
            'username': 'mitali',
            'password': 'mitali',
            'is_admin': False
        },
        {
            'name': 'Tanvi Bafna',
            'username': 'tanvi',
            'password': 'tanvi',
            'is_admin': False
        }
    ]

    for user in addUsers:

        # Check if the user already exists
        if User.query.filter_by(username=user['username']).first():
            continue

        # Create a new user object
        new_user = User(
            name=user['name'],
            username=user['username'],
            password_hash=generate_password_hash(user['password']),
            is_admin=user['is_admin'],
        )

        # Add the new user to the database
        db.session.add(new_user)
        try:
            db.session.commit()
            print(f'User {user["username"]} successfully created!')
        except Exception as e:
            db.session.rollback()
