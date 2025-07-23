from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv
import os

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY')

    from .auth.routes import auth_bp
    from .users.routes import users_bp
    from .books.routes import books_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(books_bp)

    return app