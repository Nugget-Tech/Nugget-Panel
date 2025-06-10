from flask import Flask
from .blueprints.auth import auth_bp
from .blueprints.dashboard import dashboard_bp
from .blueprints.api import api_bp
from .blueprints.landing import landing_bp
from .extensions import settings_manager, Helpers
import os


def create_app():
    app = Flask(__name__)
    app.secret_key = os.urandom(24)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(landing_bp)

    # Initialize settings manager
    init_settings()

    return app


def init_settings():
    """Initialize settings for all bots"""
    try:
        # Get list of bots from bots.json
        bots = Helpers.list_nuggets()

        # For each bot, ensure all settings categories have defaults
        for bot in bots:
            bot_id = bot.get("alias")
            if bot_id:
                # for category in settings_manager.defaults.keys():
                # if not settings_manager.get_settings(bot_id, category):
                # settings_manager.reset_settings(bot_id, category)
                print("To be converted to automatic bot rehydrator. DO NOT IGNORE.")
    except Exception as e:
        print(f"Error initializing settings: {e}")
