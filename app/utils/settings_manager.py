from pathlib import Path
import json
from typing import Any, Dict, Optional
import logging


class SettingsManager:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.settings_dir = data_dir / "settings"
        self.settings_dir.mkdir(exist_ok=True)

        # Default settings for each category
        self.defaults = {
            "aiModel": "models/gemini-2.0-flash-lite",
            "maxContext": "20",
            "filterSexuallyExplicit": "BLOCK_NONE",
            "filterHarassment": "BLOCK_NONE",
            "filterDangerous": "BLOCK_NONE",
            "filterHateSpeech": "BLOCK_NONE",
            "filterUnspecified": "BLOCK_MEDIUM_AND_ABOVE",
            "temperature": "0",
            "topP": "0.95",
            "topK": "40",
            "memoryWindow": "50",
            "contextWindow": "8192",
            "wack_message": "Ow! Uhh, what were we talking about?",
            "wack_error": "Sorry, can't remove what's not there. :joy:",
            "error_message": "Nuh uh, not gonna happen.",
            "activate_message": "Hey! I'm new here :wave:",
            "deactivate_message": "Awh, sorry to see you go! You can still talk to me by pinging me :pleading_face:",
            "voiceModel": "eleven_flash_v2_5",
            "recording-time": "10",
            "deepContext": "on",
            "freewill": "off",
            "textFrequency": "0",
            "keywordChance": "0",
            "keywords": [],
            "voiceMessages": "off",
            "voiceMessageConvo": "on",
            "voiceChance": "100",
            "debugMode": True,
        }
