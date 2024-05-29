from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from .models import db

import os
import base64
from dotenv import load_dotenv
load_dotenv()

from .utils import populate_db

#-------------------

login_manager = LoginManager()

def create_app():
    app = Flask(__name__, template_folder='templates')
    app.config['SECRET_KEY'] = base64.b64decode(os.getenv('SECRET_KEY'))

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)

    from .routes import main
    app.register_blueprint(main)

    return app

app = create_app()
with app.app_context():
    db.create_all()
    # Add users to the database
    if bool(os.getenv('DEBUG')):
        populate_db()
        