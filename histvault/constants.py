"""
Copyright 2026 HistVault Open Source Project Contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import platform
from pathlib import Path

APP_NAME = "HistVault"
APP_VERSION = "1.0.0"

# Default local vault storage directory
DEFAULT_VAULT_DIR = Path.home() / ".histvault"
DEFAULT_DB_PATH = DEFAULT_VAULT_DIR / "vault.db"

# Default web server configuration
DEFAULT_SERVER_HOST = "127.0.0.1"
DEFAULT_SERVER_PORT = 8765

# Epoch offsets
# Chromium WebKit epoch: microseconds since Jan 1, 1601 UTC
WEBKIT_EPOCH_DIFF_SECONDS = 11644473600

# Browser history locations across Operating Systems
CURRENT_OS = platform.system()

def get_browser_search_paths() -> dict:
    """Returns detected default profile paths for supported browsers."""
    paths = {
        "chrome": [],
        "edge": [],
        "brave": [],
        "firefox": [],
        "opera": [],
        "vivaldi": []
    }

    if CURRENT_OS == "Windows":
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        app_data = os.environ.get("APPDATA", "")

        if local_app_data:
            paths["chrome"].append(Path(local_app_data) / "Google" / "Chrome" / "User Data")
            paths["edge"].append(Path(local_app_data) / "Microsoft" / "Edge" / "User Data")
            paths["brave"].append(Path(local_app_data) / "BraveSoftware" / "Brave-Browser" / "User Data")
            paths["vivaldi"].append(Path(local_app_data) / "Vivaldi" / "User Data")

        if app_data:
            paths["firefox"].append(Path(app_data) / "Mozilla" / "Firefox" / "Profiles")
            paths["opera"].append(Path(app_data) / "Opera Software" / "Opera Stable")
            paths["opera"].append(Path(app_data) / "Opera Software" / "Opera GX Stable")

    elif CURRENT_OS == "Darwin":  # macOS
        home = Path.home()
        paths["chrome"].append(home / "Library" / "Application Support" / "Google" / "Chrome")
        paths["edge"].append(home / "Library" / "Application Support" / "Microsoft Edge")
        paths["brave"].append(home / "Library" / "Application Support" / "BraveSoftware" / "Brave-Browser")
        paths["firefox"].append(home / "Library" / "Application Support" / "Firefox" / "Profiles")
        paths["opera"].append(home / "Library" / "Application Support" / "com.operasoftware.Opera")
        paths["vivaldi"].append(home / "Library" / "Application Support" / "Vivaldi")

    elif CURRENT_OS == "Linux":
        home = Path.home()
        paths["chrome"].append(home / ".config" / "google-chrome")
        paths["edge"].append(home / ".config" / "microsoft-edge")
        paths["brave"].append(home / ".config" / "BraveSoftware" / "Brave-Browser")
        paths["firefox"].append(home / ".mozilla" / "firefox")
        paths["opera"].append(home / ".config" / "opera")
        paths["vivaldi"].append(home / ".config" / "vivaldi")

    return paths

# Domain categories dictionary for automatic tagging
DEFAULT_CATEGORY_RULES = {
    "Development & Tech": [
        "github.com", "gitlab.com", "stackoverflow.com", "pypi.org", "npmjs.com",
        "docs.python.org", "developer.mozilla.org", "w3schools.com", "medium.com",
        "dev.to", "docker.com", "kubernetes.io", "aws.amazon.com", "cloud.google.com"
    ],
    "Search & Reference": [
        "google.com", "bing.com", "duckduckgo.com", "wikipedia.org", "chatgpt.com",
        "claude.ai", "gemini.google.com", "perplexity.ai", "wolframalpha.com", "archive.org"
    ],
    "Social & Communication": [
        "twitter.com", "x.com", "reddit.com", "facebook.com", "instagram.com",
        "linkedin.com", "discord.com", "telegram.org", "whatsapp.com", "threads.net"
    ],
    "Media & Streaming": [
        "youtube.com", "netflix.com", "spotify.com", "twitch.tv", "vimeo.com",
        "soundcloud.com", "disneyplus.com", "primevideo.com", "tiktok.com"
    ],
    "Shopping & Finance": [
        "amazon.com", "ebay.com", "tokopedia.com", "shopee.com", "aliexpress.com",
        "paypal.com", "binance.com", "coinbase.com", "stripe.com"
    ],
    "News & Articles": [
        "cnn.com", "bbc.com", "theverge.com", "techcrunch.com", "nytimes.com",
        "bloomberg.com", "reuters.com", "kompas.com", "detik.com"
    ]
}
