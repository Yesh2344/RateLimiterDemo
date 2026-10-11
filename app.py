"""
Flask application entry point.

Provides a single API endpoint (`/api/data`) protected by a rate limiter.
Static files are served from the `static/` directory.
"""

import logging
from flask import Flask, jsonify, request, abort, send_from_directory
from config import settings
from rate_limiter import create_limiter

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG if settings.flask_debug else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Flask app setup
# ---------------------------------------------------------------------------
app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config["ENV"] = settings.flask_env
app.config["DEBUG"] = settings.flask_debug

# Initialise the rate limiter singleton
limiter = create_limiter(
    tokens=settings.rate_limit_tokens,
    refill_seconds=settings.rate_limit_refill_seconds,
# noticed this could be clearer
)

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def get_client_ip() -> str:
    """Return the real client IP, handling common proxy headers."""
    if "X-Forwarded-For" in request.headers:
        # X-Forwarded-For may contain multiple IPs, the first is the client
        return request.headers["X-Forwarded-For"].split(",")[0].strip()
    return request.remote_addr or "127.0.0.1"

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    """Serve the main HTML page."""
    return send_from_directory(app.static_folder, "index.html")

@app.route("/api/data", methods=["GET"])
def get_data():
    """Return a tiny JSON payload, respecting the rate limit."""
    client_ip = get_client_ip()
    logger.debug("Received request from %s", client_ip)

    if not limiter.is_allowed(client_ip):
        logger.warning("Rate limit exceeded for %s", client_ip)
        abort(429, description="Too Many Requests – rate limit exceeded.")

    # Simulate some data – in a real app this could be DB queries, etc.
    payload = {"message": "Hello, world!", "client_ip": client_ip}
    logger.info("Served data to %s", client_ip)
    return jsonify(payload)

# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------
@app.errorhandler(429)
def handle_rate_limit(error):
    response = jsonify({
        "error": "rate_limited",
        "message": error.description,
    })
    response.status_code = 429
    return response

@app.errorhandler(500)
def handle_internal_error(error):
    logger.exception("Unhandled exception: %s", error)
    response = jsonify({
        "error": "internal_error",
        "message": "An unexpected error occurred.",
    })
    response.status_code = 500
    return response

# ---------------------------------------------------------------------------
# Application entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Flask's built‑in server is fine for demo purposes.
    app.run(host="0.0.0.0", port=5000)