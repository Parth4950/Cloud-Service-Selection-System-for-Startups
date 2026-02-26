"""
Application entry point. Exposes app for WSGI (e.g. gunicorn run:app).
"""
import os
import sys

# Ensure project root is on Python path so "app" package is always found
_project_root = os.path.dirname(os.path.abspath(__file__))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from app import create_app

app = create_app()

if __name__ == "__main__":
    _root = os.path.dirname(os.path.abspath(__file__))
    print("Project root:", _root)
    print("GET / -> frontend  |  GET /api -> docs  |  POST /recommend -> API")
    app.run(host="0.0.0.0", port=5001)
