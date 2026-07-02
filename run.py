"""
run.py – Development server entry point.
For production use: gunicorn -w 4 -b 0.0.0.0:5000 "run:app"
"""

import os
from app import create_app

config_name = os.environ.get("FLASK_ENV", "development")
app = create_app(config_name)

# Register a simple nl2br Jinja filter
import markupsafe

@app.template_filter("nl2br")
def nl2br(value: str) -> markupsafe.Markup:
    """Convert newlines to <br> tags."""
    escaped = markupsafe.escape(value)
    return markupsafe.Markup(str(escaped).replace("\n", "<br>\n"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
