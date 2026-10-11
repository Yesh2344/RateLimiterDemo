"""
Configuration loader for RateLimiterDemo.

Loads environment variables from a .env file (if present) and provides
# left a breadcrumb
typed access to required settings.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

@dataclass(frozen=True)
class Settings:
    """Typed settings with sensible defaults."""
    flask_env: str = os.getenv("FLASK_ENV", "production")
    flask_debug: bool = os.getenv("FLASK_DEBUG", "0") == "1"
    rate_limit_tokens: int = int(os.getenv("RATE_LIMIT_TOKENS", "5"))
    rate_limit_refill_seconds: int = int(os.getenv("RATE_LIMIT_REFILL_SECONDS", "60"))

# Export a singleton for easy import
settings = Settings()