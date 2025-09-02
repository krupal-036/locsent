from flask import Flask
from dotenv import load_dotenv
import os
from extensions import bcrypt, login_manager
from models import User
from flask_wtf.csrf import CSRFProtect

def create_app():
    """Application Factory Function"""
    load_dotenv()

    app = Flask(
        __name__,
        static_folder='static',
        template_folder='templates'
    )


    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')

    csrf = CSRFProtect(app)

    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)

    from auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app