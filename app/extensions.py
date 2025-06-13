from functools import wraps
from flask import session, request, redirect, url_for, jsonify
import requests
import json
from pathlib import Path
import uuid
import logging
from dotenv import load_dotenv
import os
import docker
import re
import datetime

docker_client = docker.from_env()


load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Discord OAuth2 credentials
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://localhost:5000/auth/callback"
API_BASE_URL = "https://discord.com/api"
AUTHORIZATION_BASE_URL = "https://discord.com/api/oauth2/authorize"
TOKEN_URL = "https://discord.com/api/oauth2/token"
# TODO: UNIFY IN .env

# Data storage paths
DATA_DIR = Path("data")
PERSONALITY_DATA_DIR = DATA_DIR / "personality_traits"
BOTS_FILE = DATA_DIR / "bots.json"
SETTINGS_DATA_DIR = DATA_DIR / "settings"

# Create data directories
DATA_DIR.mkdir(exist_ok=True)
PERSONALITY_DATA_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Initialize bots.json if it doesn't exist
if not BOTS_FILE.exists():
    with open(BOTS_FILE, "w") as f:
        json.dump([], f)


class Helpers:
    def requires_auth(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            # Check if "token" is in the session
            if "token" not in session:
                token = request.cookies.get("token")
                if token:
                    session["token"] = token
                else:
                    return redirect(url_for("auth.login"))
            return func(*args, **kwargs)

        return decorated_function

    def get_user_data():
        headers = {"Authorization": f"Bearer {session['token']}"}
        response = requests.get(f"{API_BASE_URL}/users/@me", headers=headers)
        guilds = requests.get(f"{API_BASE_URL}/users/@me/guilds", headers=headers)
        guilds = guilds.json()
        user_data = response.json()
        print("User data: ", user_data)
        return user_data

    def get_guilds():
        headers = {"Authorization": f"Bearer {session['token']}"}
        guilds = requests.get(f"{API_BASE_URL}/users/@me/guilds", headers=headers)
        guilds = guilds.json()
        return guilds

    # https://cdn.discordapp.com/icons/<guild_id>/<guild_icon_hash>.png

    def list_nuggets():
        try:
            if not BOTS_FILE.exists():
                logger.warning(
                    f"Bots file not found at {BOTS_FILE}, creating empty file"
                )
                with open(BOTS_FILE, "w") as f:
                    json.dump([], f)
                return []

            with open(BOTS_FILE, "r") as f:
                bots = json.load(f)
                logger.info(f"Successfully loaded {len(bots)} bots from {BOTS_FILE}")
                return bots
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding bots.json: {e}")
            return []
        except Exception as e:
            logger.error(f"Error loading bots: {e}")
            return []

    def save_nugget(bot_data, secret_data):
        try:
            if not bot_data or "name" not in bot_data:
                logger.error("Bot data is missing required 'name' field")
                return False, None

            logger.info(f"Saving bot data: {bot_data}")
            bots = Helpers.list_nuggets()
            if bots is None:
                bots = []

            # Generate a unique alias if not provided
            if "alias" not in bot_data:
                bot_data["alias"] = str(uuid.uuid4())
                logger.info(f"Generated new alias for bot: {bot_data['alias']}")
                if not Helpers._create_bot_container(bot_data, secret_data):
                    raise Exception("Failed to create bot container")

            # Update existing bot or add new one
            updated = False
            for i, bot in enumerate(bots):
                if bot.get("name") == bot_data["name"]:
                    bots[i].update(bot_data)
                    updated = True
                    logger.info(f"Updated existing bot: {bot_data['name']}")
                    break

            if not updated:
                bots.append(bot_data)
                logger.info(f"Added new bot: {bot_data['name']}")

            BOTS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(BOTS_FILE, "w") as f:
                json.dump(bots, f, indent=4)
                logger.info(f"Successfully saved bots to {BOTS_FILE}")

            return (
                True,
                bot_data["alias"],
            )  # this must be split off, token goes into the json file

        except Exception as e:
            logger.error(f"Error saving bot: {e}")
            return False, None

    def _create_bot_container(bot_data, secret_data):
        container = None
        base_port = 10000
        port = base_port + hash(bot_data["alias"]) % 10000
        try:
            # Run the bot container with the volume
            container = docker_client.containers.run(
                image="discord-bot",
                name=f"{bot_data['alias']}",
                volumes={
                    "nugget-dockerized": {
                        # "bind": f"/app/data/{bot_data['alias']}/",  # BIND THE BOTS DIRECTORY ONLY
                        "bind": f"/app/data",
                        "mode": "rw",
                    }
                },
                ports={"8000/tcp": port},  # Dynamically assign a host port
                detach=True,  # Run in background
                environment={
                    "BOT_ID": bot_data["alias"],
                    "DATA_DIR": f"/app/data",
                    "alias": bot_data["alias"],
                    "gemini_api_key": secret_data["gemini_api_key"],
                    "elevenlabs_api_key": secret_data["elevenlabs_api_key"],
                    "discord_token": secret_data["discord_token"],
                },
            )

            # Wait for container to start and get port
            import time

            for _ in range(5):  # Try 5 times
                container.reload()
                ports = container.attrs.get("NetworkSettings", {}).get("Ports", {})
                if ports and "8000/tcp" in ports and ports["8000/tcp"]:
                    host_port = ports["8000/tcp"][0].get("HostPort")
                    if host_port:
                        logger.info(f"Bot exposed on host port: {host_port}")
                        bot_data["port"] = host_port
                        logger.info(f"Started Docker container for bot: {container.id}")
                        return True
                time.sleep(1)

            raise Exception("Could not obtain container port after multiple attempts")

        except Exception as e:
            logger.error(f"Error in container setup: {e}")
            if container:
                try:
                    # container.remove(force=True)
                    logger.info(
                        f"Cleaned up failed container for bot: {bot_data['alias']}"
                    )
                except Exception as cleanup_error:
                    logger.error(f"Error cleaning up container: {cleanup_error}")
            return False

    def delete_nugget(bot_name):
        try:
            bots = Helpers.list_nuggets()
            bots = [b for b in bots if b["name"] != bot_name]

            with open(BOTS_FILE, "w") as f:
                json.dump(bots, f, indent=4)

            # Delete associated personality file if it exists
            personality_file = PERSONALITY_DATA_DIR / f"{bot_name}.json"
            if personality_file.exists():
                personality_file.unlink()

            return True
        except Exception as e:
            print(f"Error deleting bot: {e}")
            return False

    def save_config(bot_name, config):
        """Save configuration for a bot"""
        try:
            # Find bot in bots.json to get URL
            bots_file_path = DATA_DIR / "bots.json"
            with open(bots_file_path, "r") as ul_bots_file:
                bots_file = json.load(ul_bots_file)
                url = None
                for bot in bots_file:
                    if bot["alias"] == bot_name:
                        url = f"http://localhost:{bot['port']}"
                        break

            if not url:
                logger.error(f"Bot {bot_name} not found in bots.json")
                raise ValueError(f"Bot {bot_name} not found")

            # Ensure config is a dict
            if not isinstance(config, dict):
                try:
                    config = (
                        json.loads(config)
                        if isinstance(config, str)
                        else {"config": config}
                    )
                except (json.JSONDecodeError, AttributeError):
                    config = {"config": config}

            # Save config directly to settings/{bot_id}.json
            config_path = SETTINGS_DATA_DIR / f"{bot_name}.json"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w") as json_file:
                json.dump(config, json_file, indent=4)

            # Notify bot of config update
            requests.post(
                f"{url}/event",
                json={"type": "update_config", "config": config},
                timeout=5,
            )

        except Exception as e:
            logger.error(f"Error saving config for {bot_name}: {e}")
            raise

    def get_config(bot_name):
        """Get configuration for a bot"""
        try:
            config_path = SETTINGS_DATA_DIR / f"{bot_name}.json"
            if not config_path.exists():
                return {}
            with open(config_path, "r") as json_file:
                return json.load(json_file)
        except Exception as e:
            logger.error(f"Error getting config for {bot_name}: {e}")
            return {}

    def save_personality(bot_name, personality):
        with open("./data/bots.json", "r") as ul_bots_file:
            bots_file: dict = json.load(ul_bots_file)
            for bot in bots_file:
                if bot["alias"] == bot_name:
                    # meaning we've found the bot
                    url = f"http://localhost:{bot['port']}"
        try:
            # Try to load existing personality
            existing_personality = {}
            personality_path = PERSONALITY_DATA_DIR / f"{bot_name}.json"
            if personality_path.exists():
                with open(personality_path, "r") as json_file:
                    existing_personality = json.load(json_file)

            # Update existing personality with new data
            if isinstance(personality, dict):
                existing_personality.update(personality)
                partial_transformed_personality = Helpers.transform_bot_json(
                    personality
                )
                requests.post(
                    f"{url}/event",
                    json={
                        "type": "update_personality",
                        "personality": Helpers.split_personality_updates(
                            partial_transformed_personality
                        ),
                    },
                )
            else:
                # If personality is not a dict, try to parse it as JSON first
                try:
                    personality_dict = (
                        json.loads(personality)
                        if isinstance(personality, str)
                        else personality
                    )
                    existing_personality.update(personality_dict)
                    partial_transformed_personality = Helpers.transform_bot_json(
                        personality_dict
                    )
                    requests.post(
                        f"{url}/event",
                        json={
                            "type": "update_personality",
                            "personality": Helpers.split_personality_updates(
                                partial_transformed_personality
                            ),
                        },
                    )
                except (json.JSONDecodeError, AttributeError):
                    # If parsing fails, store it as is under a default key
                    existing_personality["personality"] = personality

            # Save the merged personality
            with open(personality_path, "w") as json_file:
                json.dump(existing_personality, json_file, indent=4)

        except Exception as e:
            logger.error(f"Error saving personality for {bot_name}: {e}")
            raise

    def get_personality(bot_name):
        try:
            with open(f"{PERSONALITY_DATA_DIR}/{bot_name}.json", "r") as json_file:
                return json.load(json_file)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing personality for {bot_name}: {e}")
            return {}

    def transform_bot_json(input_json, bot_name):
        """Keep as internal function"""
        # Extract all example indices
        example_pattern = re.compile(r"examples\[(\d+)\]\.(user|bot)")
        example_indices = set()

        for key in input_json.keys():
            match = example_pattern.match(key)
            if match:
                example_indices.add(int(match.group(1)))

        # Build conversation examples sorted by index
        conversation_examples = []
        for i in sorted(example_indices):
            user_key = f"examples[{i}].user"
            bot_key = f"examples[{i}].bot"
            conversation_examples.append(
                {
                    "user": input_json.get(user_key, ""),
                    "bot": input_json.get(bot_key, ""),
                }
            )

        # Compose output JSON
        output_json = {
            "personality_traits": {
                "name": input_json.get("name", ""),
                "age": int(input_json.get("age", 0)),
                "role": input_json.get("role", ""),
                "description": input_json.get("description", ""),
                "likes": input_json.get("likes", ""),
                "dislikes": input_json.get("dislikes", ""),
            },
            "system_note": input_json.get("systemNote", ""),
            "conversation_examples": conversation_examples,
        }

        personality_file = PERSONALITY_DATA_DIR / f"{bot_name}.json"
        with open(personality_file, "w") as f:
            json.dump(output_json, f, indent=4)

        return output_json

    def _split_personality_updates(full_json):
        updates = []

        # Personality traits
        for key, value in full_json["personality_traits"].items():
            updates.append({"personality_traits": {key: value}})

        # System note
        updates.append({"system_note": full_json.get("system_note", "")})

        # Conversation examples (send separately if needed, or skip if not supported)
        # If needed:
        convo_eg = []
        for i, example in enumerate(full_json.get("conversation_examples", [])):
            convo_eg.append({"user": example["user"], "bot": example["bot"]})
            updates.append({"conversation_examples": convo_eg})

        return updates

    def split_personality_updates(full_json):
        updates = {}

        # Personality traits
        personality_traits = {}
        for key, value in full_json.get("personality_traits", {}).items():
            personality_traits[key] = value
        if personality_traits:
            updates["personality_traits"] = personality_traits

        # System note
        system_note = full_json.get("system_note")
        if system_note is not None:
            updates["system_note"] = system_note

        # Conversation examples
        conversation_examples = []
        for example in full_json.get("conversation_examples", []):
            conversation_examples.append(
                {"user": example["user"], "bot": example["bot"]}
            )
        if conversation_examples:
            updates["conversation_examples"] = conversation_examples

        return updates

    def merge_updates(update_list):
        merged = {}
        for update in update_list:
            for key, value in update.items():
                if (
                    key in merged
                    and isinstance(merged[key], list)
                    and isinstance(value, list)
                ):
                    merged[key].extend(value)
                elif (
                    key in merged
                    and isinstance(merged[key], dict)
                    and isinstance(value, dict)
                ):
                    merged[key].update(value)
                else:
                    merged[key] = value
        return merged

    def get_memories(bot_name) -> dict:
        # Find bot in bots.json to get URL
        bots_file_path = DATA_DIR / "bots.json"
        with open(bots_file_path, "r") as ul_bots_file:
            bots_file = json.load(ul_bots_file)
            url = None
            for bot in bots_file:
                if bot["alias"] == bot_name:
                    url = f"http://localhost:{bot['port']}"
                    break

        if not url:
            logger.error(f"Bot {bot_name} not found in bots.json")
            raise ValueError(f"Bot {bot_name} not found")

        return json.loads(requests.get(f"{url}/memories").text)

    def get_bot_guilds(bot_name):
        bots_file_path = DATA_DIR / "bots.json"
        with open(bots_file_path, "r") as ul_bots_file:
            bots_file = json.load(ul_bots_file)
            url = None
            for bot in bots_file:
                if bot["alias"] == bot_name:
                    url = f"http://localhost:{bot['port']}"
                    break

        if not url:
            logger.error(f"Bot {bot_name} not found in bots.json")
            raise ValueError(f"Bot {bot_name} not found")

        return json.loads(requests.get(f"{url}/guilds").text)

    def save_memory(bot_name, guild_id, special_phrase, memory_content, memory_id):
        # Find bot in bots.json to get URL
        bots_file_path = DATA_DIR / "bots.json"
        with open(bots_file_path, "r") as ul_bots_file:
            bots_file = json.load(ul_bots_file)
            url = None
            for bot in bots_file:
                if bot["alias"] == bot_name:
                    url = f"http://localhost:{bot['port']}"
                    break

        if not url:
            logger.error(f"Bot {bot_name} not found in bots.json")
            raise ValueError(f"Bot {bot_name} not found")

        # Send POST request to /event endpoint with update_memory event
        if memory_id == None or memory_id == "":
            memory_uuid = str(uuid.uuid4())
        else:
            memory_uuid = memory_id
        response = requests.post(
            f"{url}/event",
            json={
                "type": "update_memory",
                "memory": {
                    f"{guild_id}": [
                        {
                            "guild_id": guild_id,
                            "memory_id": memory_uuid,
                            "special_phrase": special_phrase,
                            "memory": memory_content,
                            "timestamp": datetime.datetime.now().isoformat(),
                        }
                    ],
                },
            },
        )
        return json.loads(response.text), memory_id

    def delete_memory(bot_name, guild_id, memory_id):
        # Find bot in bots.json to get URL
        bots_file_path = DATA_DIR / "bots.json"
        with open(bots_file_path, "r") as ul_bots_file:
            bots_file = json.load(ul_bots_file)
            url = None
            for bot in bots_file:
                if bot["alias"] == bot_name:
                    url = f"http://localhost:{bot['port']}"
                    break

        if not url:
            logger.error(f"Bot {bot_name} not found in bots.json")
            raise ValueError(f"Bot {bot_name} not found")

        # Send POST request to /event endpoint with update_memory event

        response = requests.post(
            f"{url}/event",
            json={
                "type": "delete_memory",
                "memory": {
                    f"{guild_id}": [
                        {
                            "memory_id": memory_id,
                        }
                    ],
                },
            },
        )
        print(response.text)
        return jsonify({"memory_id": memory_id, "response": str(response.json)})

    def fetch_invite(bot_name):
        bots_file_path = DATA_DIR / "bots.json"
        with open(bots_file_path, "r") as ul_bots_file:
            bots_file = json.load(ul_bots_file)
            url = None
            for bot in bots_file:
                if bot["alias"] == bot_name:
                    url = f"http://localhost:{bot['port']}"
                    break

        if not url:
            logger.error(f"Bot {bot_name} not found in bots.json")
            raise ValueError(f"Bot {bot_name} not found")

        response = requests.get(f"{url}/bot-details")
        print(response)
        return f"https://discord.com/oauth2/authorize?client_id={response.json().get("bot_id")}&permissions=309240907840&integration_type=0&scope=bot"


# Initialize settings manager
from .utils.settings_manager import SettingsManager

settings_manager = SettingsManager(DATA_DIR)
