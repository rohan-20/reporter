import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "reporter"
CONFIG_FILE = CONFIG_DIR / "config.json"

def _load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def _save_config(data: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

def save_token(token: str):
    config = _load_config()
    config["GITHUB_TOKEN"] = token
    _save_config(config)
    print(f"✅ Token saved to {CONFIG_FILE}")

def load_token() -> str | None:
    return _load_config().get("GITHUB_TOKEN")

def save_api(api: str):
    config = _load_config()
    config["GROQ_API_KEY"] = api
    _save_config(config)
    print(f"✅ Groq API Key saved to {CONFIG_FILE}")

def load_api() -> str | None:
    return _load_config().get("GROQ_API_KEY")
