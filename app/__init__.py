"""
Application package. Initializes Flask app via factory pattern.
"""

import logging
import os
import sys

from flask import Flask, request, jsonify, send_from_directory
from flask import current_app


def _configure_logging() -> None:
    """
    Configure Python logging for production. INFO level, stdout, format
    compatible with AWS Elastic Beanstalk log capture.
    """
    log_format = "%(asctime)s | %(levelname)s | %(module)s | %(message)s"
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(log_format))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    root.addHandler(handler)


def create_app(config=None):
    """
    Application factory. Creates and configures the Flask application.
    Registers blueprints. No business logic here.
    """
    _configure_logging()

    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _frontend = os.path.join(_root, "frontend")

    app = Flask(__name__)
    app.config["FRONTEND_DIR"] = _frontend

    if config is not None:
        app.config.update(config)

    def _frontend_path():
        return app.config["FRONTEND_DIR"]

    # Register "/" and static assets FIRST so they win over blueprint
    @app.route("/")
    def serve_app():
        return send_from_directory(_frontend_path(), "index.html")

    def _make_asset_route(name):
        def _serve():
            return send_from_directory(_frontend_path(), name)
        return _serve

    for _asset in ("style.css", "script.js", "api.js", "ui.js"):
        app.add_url_rule("/" + _asset, "frontend_" + _asset.replace(".", "_"), _make_asset_route(_asset))

    _frontend_lib = os.path.join(_frontend, "lib")

    @app.route("/lib/<path:filename>")
    def serve_lib(filename):
        return send_from_directory(_frontend_lib, filename)

    @app.route("/api")
    def api_docs():
        return jsonify({
            "service": "Cloud provider recommendation API",
            "endpoint": "POST /recommend",
            "docs": "Send a JSON body with: budget, scalability, security, ease_of_use, free_tier, team_expertise, industry",
        })

    # Blueprint after app routes so /health, /recommend don't override /
    from app.routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            resp = current_app.make_response(("", 204))
            resp.headers["Access-Control-Allow-Origin"] = "*"
            resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
            resp.headers["Access-Control-Max-Age"] = "86400"
            return resp

    return app
