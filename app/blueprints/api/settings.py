from flask import jsonify, request
from . import api_bp
from ...extensions import Helpers, settings_manager


@api_bp.route("/settings/<nugget>/<category>", methods=["GET"])
@Helpers.requires_auth
def get_settings(nugget, category):
    """Get settings for a specific nugget and category."""
    return


@api_bp.route("/settings/<nugget>/<category>", methods=["POST"])
@Helpers.requires_auth
def save_settings(nugget, category):
    """Save settings for a specific nugget and category."""
    return


@api_bp.route("/settings/<nugget>/<category>/reset", methods=["POST"])
@Helpers.requires_auth
def reset_settings(nugget, category):
    return


@api_bp.route("/validate-key", methods=["POST"])
@Helpers.requires_auth
def validate_api_key():
    return
