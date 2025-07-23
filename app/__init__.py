from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv
import os

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY')

    # Import blueprints and the oauth object
    from .auth.routes import auth_bp, oauth  # <-- Import oauth here
    from .users.routes import users_bp
    from .books.routes import books_bp

    # Initialize oauth with the app
    oauth.init_app(app)  # <-- Add this line

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(books_bp)

    return app