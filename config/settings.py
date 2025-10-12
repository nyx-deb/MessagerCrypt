"""
Configuration settings for MessagerCrypt
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Database settings
DATABASE_PATH = DATA_DIR / "messagercrypt.db"
DATABASE_KEY = os.environ.get("MESSAGERCRYPT_DB_KEY", "default_key_change_me")

# Network settings
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8888
MAX_CONNECTIONS = 10
BUFFER_SIZE = 4096

# Security settings
RSA_KEY_SIZE = 4096
AES_KEY_SIZE = 32  # 256 bits
NONCE_SIZE = 12    # 96 bits for GCM
SALT_SIZE = 32     # 256 bits
ITERATIONS = 100000  # For Argon2

# Message settings
MAX_MESSAGE_LENGTH = 1000
MESSAGE_TIMEOUT = 30  # seconds

# UI settings
ANIMATION_SPEED = 0.1
COLORS = {
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "white": "\033[97m",
    "bold": "\033[1m",
    "reset": "\033[0m"
}

# Debug mode
DEBUG = os.environ.get("MESSAGERCRYPT_DEBUG", "false").lower() == "true"

# Logging
LOG_LEVEL = "DEBUG" if DEBUG else "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
