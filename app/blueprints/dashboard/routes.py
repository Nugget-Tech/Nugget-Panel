from flask import render_template, request
from . import dashboard_bp
from ...extensions import Helpers
import logging
from google import genai
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv
import os

load_dotenv()

logger = logging.getLogger(__name__)
gemini_client = genai.Client(api_key=os.getenv("API_KEY"))  # TODO: UNIFY IN .env
elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))


# Main routes
@dashboard_bp.route("/home")
@Helpers.requires_auth
def home():
    try:
        user_data = Helpers.get_user_data()
        nuggets = Helpers.list_nuggets()
        logger.info(f"Loaded {len(nuggets)} bots for user {user_data['username']}")

        return render_template(
            "dashboard/home.html",
            username=user_data["username"],
            avatar_url=f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png",
            nuggets=nuggets,
        )
    except Exception as e:
        logger.error(f"Error in home route: {e}")
        return render_template(
            "dashboard/home.html",
            username="User",
            avatar_url="https://cdn.discordapp.com/embed/avatars/0.png",
            nuggets=[],
            error="Failed to load bots. Please try again later.",
        )


# Bot-specific routes
@dashboard_bp.route("/<nugget>/dashboard")
@Helpers.requires_auth
def dashboard(nugget):
    user_data = Helpers.get_user_data()
    if any(
        item in request.args
        for item in [
            "debugMode",
            "JustGetRidOfTheName",
        ]
    ):  # this checks to see if any of the items that can change have changed, if so we need to check to see which one of these is none
        # then we need to check to see if any of these items have a corresponding value in a databank, if they do and the request argument is none
        # then we can safely ignore it and retain the original item
        print("Checking to see which item is not none")
        new_config = {}
        for item in request.args:
            if request.args.get(item) != "":
                new_config[item] = request.args.get(item)
        Helpers.save_config(nugget, config=new_config)
    return render_template(
        "dashboard/dashboard.html",
        nugget_alias=nugget,
        username=user_data["username"],
        avatar_url=f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png",
        personality=Helpers.get_personality(bot_name=nugget),
        settings=Helpers.get_config(bot_name=nugget),
    )


@dashboard_bp.route("/<nugget>/settings")
@Helpers.requires_auth
def settings(nugget):
    user_data = Helpers.get_user_data()
    return render_template(
        "dashboard/settings.html",
        nugget_alias=nugget,
        username=user_data["username"],
        avatar_url=f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png",
    )


@dashboard_bp.route("/<nugget>/memories")
@Helpers.requires_auth
def memories(nugget):
    user_data = Helpers.get_user_data()
    return render_template(
        "dashboard/memories.html",
        nugget_alias=nugget,
        username=user_data["username"],
        avatar_url=f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png",
    )


@dashboard_bp.route("/<nugget>/knowledge")
@Helpers.requires_auth
def knowledge(nugget):
    user_data = Helpers.get_user_data()
    return render_template(
        "dashboard/knowledge.html",
        nugget_alias=nugget,
        username=user_data["username"],
        avatar_url=f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png",
    )


# AI routes
@dashboard_bp.route("/<nugget>/ai/filters")
@Helpers.requires_auth
def ai_filters(nugget):
    user_data = Helpers.get_user_data()
    if any(
        item in request.args
        for item in [
            "filterSexuallyExplicit",
            "filterHarassment",
            "filterDangerous",
            "filterHateSpeech",
            "filterUnspecified",
        ]
    ):  # this checks to see if any of the items that can change have changed, if so we need to check to see which one of these is none
        # then we need to check to see if any of these items have a corresponding value in a databank, if they do and the request argument is none
        # then we can safely ignore it and retain the original item
        print("Checking to see which item is not none")
        new_config = {}
        for item in request.args:
            if request.args.get(item) != "":
                new_config[item] = request.args.get(item)
        Helpers.save_config(nugget, config=new_config)

    return render_template(
        "dashboard/ai/filters.html",
        nugget_alias=nugget,
        username=user_data["username"],
        avatar_url=f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png",
        settings=Helpers.get_config(nugget),
    )


@dashboard_bp.route("/<nugget>/ai/generation")
@Helpers.requires_auth
def ai_generation(nugget):
    user_data = Helpers.get_user_data()
    if any(
        item in request.args
        for item in [
            "temperature",
            "topP",
            "topK",
            "memoryWindow",
            "contextWindow",
        ]
    ):  # this checks to see if any of the items that can change have changed, if so we need to check to see which one of these is none
        # then we need to check to see if any of these items have a corresponding value in a databank, if they do and the request argument is none
        # then we can safely ignore it and retain the original item
        print("Checking to see which item is not none")
        new_config = {}
        for item in request.args:
            if request.args.get(item) != "":
                new_config[item] = request.args.get(item)
        Helpers.save_config(nugget, config=new_config)

    return render_template(
        "dashboard/ai/generation.html",
        nugget_alias=nugget,
        username=user_data["username"],
        avatar_url=f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png",
        settings=Helpers.get_config(nugget),
    )


@dashboard_bp.route("/<nugget>/ai/model")
@Helpers.requires_auth
def ai_model(nugget):
    if any(
        item in request.args for item in ["aiModel", "maxContext"]
    ):  # this checks to see if any of the items that can change have changed, if so we need to check to see which one of these is none
        # then we need to check to see if any of these items have a corresponding value in a databank, if they do and the request argument is none
        # then we can safely ignore it and retain the original item
        print("Checking to see which item is not none")
        new_config = {}
        for item in request.args:
            if request.args.get(item) != "":
                new_config[item] = request.args.get(item)
        Helpers.save_config(nugget, config=new_config)

    user_data = Helpers.get_user_data()
    return render_template(
        "dashboard/ai/model.html",
        nugget_alias=nugget,
        username=user_data["username"],
        models=[
            m.name
            for m in gemini_client.models.list()
            if "generateContent" in m.supported_actions
        ],
        avatar_url=f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png",
        settings=Helpers.get_config(nugget),
    )


@dashboard_bp.route("/<nugget>/ai/messages")
@Helpers.requires_auth
def ai_messages(nugget):
    user_data = Helpers.get_user_data()
    if any(
        item in request.args
        for item in [
            "wack_message",
            "wack_error",
            "error_message",
            "activate_message",
            "deactivate_message",
        ]
    ):  # this checks to see if any of the items that can change have changed, if so we need to check to see which one of these is none
        # then we need to check to see if any of these items have a corresponding value in a databank, if they do and the request argument is none
        # then we can safely ignore it and retain the original item
        print("Checking to see which item is not none")
        new_config = {}
        for item in request.args:
            if request.args.get(item) != "":
                new_config[item] = request.args.get(item)
        Helpers.save_config(nugget, config=new_config)
    return render_template(
        "dashboard/ai/messages.html",
        nugget_alias=nugget,
        username=user_data["username"],
        avatar_url=f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png",
        settings=Helpers.get_config(nugget),
    )


# Personality routes
@dashboard_bp.route("/<nugget>/personality/traits")
@Helpers.requires_auth
def personality_traits(nugget):
    user_data = Helpers.get_user_data()
    if any(
        item in request.args
        for item in ["name", "age", "role", "description", "likes", "dislikes"]
    ):  # this checks to see if any of the items that can change have changed, if so we need to check to see which one of these is none
        # then we need to check to see if any of these items have a corresponding value in a databank, if they do and the request argument is none
        # then we can safely ignore it and retain the original item
        print("Checking to see which item is not none")
        new_personality = {}
        for item in request.args:
            if request.args.get(item) != "" or request.args.get(item) == None:
                new_personality[item] = request.args.get(item)
        Helpers.save_personality(nugget, personality=new_personality)
    return render_template(
        "dashboard/personality/traits.html",
        nugget_alias=nugget,
        username=user_data["username"],
        avatar_url=f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png",
        settings=Helpers.get_personality(nugget),
    )


@dashboard_bp.route("/<nugget>/personality/prompting")
@Helpers.requires_auth
def personality_prompting(nugget):
    user_data = Helpers.get_user_data()
    if any(
        item in request.args for item in ["systemNote", "examples"]
    ):  # this checks to see if any of the items that can change have changed, if so we need to check to see which one of these is none
        # then we need to check to see if any of these items have a corresponding value in a databank, if they do and the request argument is none
        # then we can safely ignore it and retain the original item
        print("Checking to see which item is not none")
        new_personality = {}
        for item in request.args:
            if request.args.get(item) != "" or request.args.get(item) == None:
                new_personality[item] = request.args.get(item)
        Helpers.save_personality(nugget, personality=new_personality)
    return render_template(
        "dashboard/personality/prompting.html",
        nugget_alias=nugget,
        username=user_data["username"],
        avatar_url=f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png",
        settings=Helpers.get_personality(nugget),
    )


@dashboard_bp.route("/<nugget>/personality/autonomy")
@Helpers.requires_auth
def personality_autonomy(nugget):
    user_data = Helpers.get_user_data()
    if any(
        item in request.args
        for item in [
            "deepContext",
            "freewill",
            "textFrequency",
            "keywordChance",
            "keywords",
        ]
    ):  # this checks to see if any of the items that can change have changed, if so we need to check to see which one of these is none
        # then we need to check to see if any of these items have a corresponding value in a databank, if they do and the request argument is none
        # then we can safely ignore it and retain the original item
        print("Checking to see which item is not none")
        new_config = {}
        for item in request.args:
            if request.args.get(item) != "":
                new_config[item] = request.args.get(item)
        Helpers.save_config(nugget, config=new_config)
    return render_template(
        "dashboard/personality/autonomy.html",
        nugget_alias=nugget,
        username=user_data["username"],
        avatar_url=f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png",
        settings=Helpers.get_config(nugget),
    )


# Features routes


@dashboard_bp.route("/<nugget>/features/memory")
@Helpers.requires_auth
def memory_config(nugget):
    user_data = Helpers.get_user_data()
    return render_template(
        "dashboard/ai/memories.html",
        nugget_alias=nugget,
        username=user_data["username"],
        avatar_url=f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png",
        guilds=Helpers.get_bot_guilds(nugget),
        # we need to firstly fetch the guilds from the bots, then fetch guilds from the user, merge the common ones into one list
    )


@dashboard_bp.route("/<nugget>/features/voice")
@Helpers.requires_auth
def features_voice(nugget):
    user_data = Helpers.get_user_data()
    if any(
        item in request.args
        for item in [
            "voiceModel",
            "voiceMessage",
            "voiceMessageConvo",
            "recording-time",
        ]
    ):  # this checks to see if any of the items that can change have changed, if so we need to check to see which one of these is none
        # then we need to check to see if any of these items have a corresponding value in a databank, if they do and the request argument is none
        # then we can safely ignore it and retain the original item
        print("Checking to see which item is not none")
        new_config = {}
        for item in request.args:
            if request.args.get(item) != "":
                new_config[item] = request.args.get(item)
        Helpers.save_config(nugget, config=new_config)
    return render_template(
        "dashboard/ai/voice.html",
        nugget_alias=nugget,
        username=user_data["username"],
        avatar_url=f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png",
        voice_models=elevenlabs_client.models.get_all(),
        settings=Helpers.get_config(nugget),
    )


@dashboard_bp.route("/<nugget>/api-keys", methods=["GET", "POST"])
@Helpers.requires_auth
def api_keys(nugget):
    user_data = Helpers.get_user_data()
    if any(
        item in request.args
        for item in ["gemini_api_key", "elevenlabs_api_key", "discord_token"]
    ):  # this checks to see if any of the items that can change have changed, if so we need to check to see which one of these is none
        # then we need to check to see if any of these items have a corresponding value in a databank, if they do and the request argument is none
        # then we can safely ignore it and retain the original item
        print("Checking to see which item is not none")
        new_config = {}
        for item in request.args:
            if request.args.get(item) != "":
                new_config[item] = request.args.get(item)
        Helpers.save_config(nugget, config=new_config)

    return render_template(
        "dashboard/authentication/api-keys.html",
        nugget_alias=nugget,
        username=user_data["username"],
        avatar_url=f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png",
        settings=Helpers.get_config(nugget),
    )
