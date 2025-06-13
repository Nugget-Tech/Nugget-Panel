from flask import Blueprint, jsonify, request, redirect
from ...extensions import Helpers, PERSONALITY_DATA_DIR
import json
import datetime

from . import api_bp


@api_bp.route("/<nugget>/personality", methods=["GET"])
@Helpers.requires_auth
def get_personality(nugget):
    try:
        json_path = PERSONALITY_DATA_DIR / f"{nugget}.json"
        if json_path.exists():
            with open(json_path, "r") as f:
                traits = json.load(f)
            return jsonify(traits)
        return jsonify({})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/<nugget>/personality", methods=["POST"])
@Helpers.requires_auth
def save_personality(nugget):
    try:
        data = request.json

        # Save to JSON file
        json_path = PERSONALITY_DATA_DIR / f"{nugget}.json"
        personality_data = {
            "bot_name": nugget,
            "name": data["name"],
            "age": data["age"],
            "role": data["role"],
            "description": data["description"],
            "likes": data["likes"],
            "dislikes": data["dislikes"],
            "last_updated": datetime.datetime.now().isoformat(),
        }

        with open(json_path, "w") as f:
            json.dump(personality_data, f, indent=4)

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/<nugget>/config", methods=["GET"])
@Helpers.requires_auth
def configure_bot(nugget):
    # This function is only meant to pull config data for this bot
    return Helpers.get_config(nugget)


@api_bp.route("/bots", methods=["POST"])
@Helpers.requires_auth
def add_bot():
    try:
        data = request.json
        bot_data = {
            "name": data["bot_name"],
            "avatar_url": data.get("avatar_url", ""),
            "bot_name": data["bot_name"],
        }

        secret_data = {
            "discord_token": data["discord_token"],
            "gemini_api_key": data["gemini_api_key"],
            "elevenlabs_api_key": data["elevenlabs_api_key"],
        }

        success, alias = Helpers.save_nugget(bot_data, secret_data)
        if success:
            # Create empty personality file
            json_path = PERSONALITY_DATA_DIR / f"{alias}.json"
            with open(json_path, "w") as f:
                json.dump(
                    {
                        "bot_name": data["bot_name"],
                        "alias": alias,
                        "last_updated": datetime.datetime.now().isoformat(),
                    },
                    f,
                    indent=4,
                )

            return jsonify({"success": True, "alias": alias})
        else:
            return jsonify({"error": "Failed to save bot"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/bots/<bot_name>", methods=["DELETE"])
@Helpers.requires_auth
def delete_bot(bot_name):
    try:
        if Helpers.delete_nugget(bot_name):
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Failed to delete bot"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/<nugget>/memories/<guild_id>", methods=["GET", "POST", "DELETE", "PUT"])
@Helpers.requires_auth
def memories(nugget, guild_id: str):
    # fetch the memory by first locating the bot's port on spine core, fetch the memories from /memories.
    match request.method:
        case "GET":
            memories = Helpers.get_memories(nugget)
            # now time to search by guild
            # simple index
            return jsonify(
                memories.get(
                    str(guild_id), {"message": f"No memories found for {guild_id}"}
                )
            )
        case "POST":
            # do something
            special_phrase = request.get_json()["special_phrase"]
            memory_content = request.get_json()["memory"]
            # generate a uuid for it and send it to the bot
            (response_message, memory_id) = Helpers.save_memory(
                bot_name=nugget,
                guild_id=guild_id,
                memory_id="",
                special_phrase=special_phrase,
                memory_content=memory_content,
            )
            return jsonify(
                {"message": f"{memory_id} Saved.", "spine_response": response_message}
            )

        case "DELETE":
            guild_id = request.get_json()["guild_id"]
            memory_id = request.get_json()["memory_id"]

            Helpers.delete_memory(
                bot_name=nugget, guild_id=guild_id, memory_id=memory_id
            )

            return jsonify(
                {
                    "message": f"{memory_id} has been deleted.",
                }
            )

        case "PUT":
            # do something
            special_phrase = request.get_json()["special_phrase"]
            memory_content = request.get_json()["memory"]
            # generate a uuid for it and send it to the bot
            (response_message, memory_id) = Helpers.save_memory(
                bot_name=nugget,
                guild_id=guild_id,
                memory_id=request.get_json()["memory_id"],
                special_phrase=special_phrase,
                memory_content=memory_content,
            )
            return jsonify(
                {"message": f"{memory_id} Saved.", "spine_response": response_message}
            )


@api_bp.route("/invite/<nugget>")
@Helpers.requires_auth
def invite_nugget(nugget):
    return redirect(Helpers.fetch_invite(nugget))
