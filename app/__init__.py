from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    # Set up login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Register blueprints
    from app.routes import auth, user, admin, booking, support, main
    app.register_blueprint(auth.bp)
    app.register_blueprint(user.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(booking.bp)
    # app.register_blueprint(support.bp)
    app.register_blueprint(main.bp)
    
     # Debug: Print all registered routes
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint} -> {rule}")
    
    
    # Create database tables
    with app.app_context():
        db.create_all()

    return app

@login_manager.user_loader
def load_user(id):
    from app.models import User
    return User.query.get(int(id))