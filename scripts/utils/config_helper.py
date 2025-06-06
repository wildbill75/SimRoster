import os
import json

CONFIG_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../config/paths.json")
)

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {
            "community_dir": "",
            "official_onestore_dir": "",
            "streamedpackages_dir": "",
        }
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
