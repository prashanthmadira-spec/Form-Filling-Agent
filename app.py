"""IntelliForm: local Flask app. Run with:  python app.py"""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from urllib.parse import urlsplit

from flask import Flask, Response, abort, jsonify, request, send_from_directory

from config import Settings
from modules.task_manager import TaskManager
from profile_manager import ProfileManager
from routes.agent_routes import create_agent_blueprint
from routes.profile_routes import create_profile_blueprint, error

DASHBOARD_FILES = {"styles.css", "app.js"}


def setup_logging(settings: Settings) -> None:
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(settings.log_dir / "intelliform.log", maxBytes=500_000, backupCount=2, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root = logging.getLogger("intelliform")
    if not any(isinstance(h, RotatingFileHandler) for h in root.handlers):
        root.addHandler(handler)
    root.setLevel(logging.INFO)


def create_app(settings: Settings | None = None, tasks: TaskManager | None = None, profiles: ProfileManager | None = None) -> Flask:
    settings = settings or Settings.from_env()
    app = Flask(__name__, static_folder=None)
    app.config["MAX_CONTENT_LENGTH"] = 1_000_000
    app.config["SETTINGS"] = settings
    app.config["SUBMIT_COUNT"] = 0  # hits on the practice forms' fake submit URL (must stay 0)
    profiles = profiles or ProfileManager(settings.data_dir)
    tasks = tasks or TaskManager(settings)
    app.config["TASKS"], app.config["PROFILES"] = tasks, profiles
    app.register_blueprint(create_profile_blueprint(profiles))
    app.register_blueprint(create_agent_blueprint(tasks, profiles))

    allowed_hosts = {urlsplit(o).netloc.lower() for o in settings.allowed_local_origins}

    @app.before_request
    def protect_api():
        # Stops other websites from driving your local agent through your browser.
        if request.method in ("POST", "PUT", "DELETE") and request.path.startswith("/api/"):
            origin = request.headers.get("Origin")
            if origin and urlsplit(origin).netloc.lower() not in allowed_hosts | {request.host.lower()}:
                return error("forbidden_origin", "Requests from other websites are not allowed.", 403)
            if request.method != "DELETE" and not request.is_json and request.get_data(cache=True):
                return error("invalid_json", "Send JSON with Content-Type: application/json.", 415)

    @app.after_request
    def headers(resp: Response):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["Referrer-Policy"] = "no-referrer"
        if request.path.startswith("/api/"):
            resp.headers["Cache-Control"] = "no-store"
        if not request.path.startswith("/test_forms/"):
            resp.headers["X-Frame-Options"] = "DENY"
            resp.headers["Content-Security-Policy"] = ("default-src 'self'; script-src 'self'; style-src 'self'; "
                                                       "img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        return resp

    # ---- static files: only an explicit allow-list is served ----
    @app.get("/")
    def index():
        return send_from_directory(settings.dashboard_dir, "index.html")

    @app.get("/<path:name>")
    def dashboard_file(name: str):
        if name in DASHBOARD_FILES:
            return send_from_directory(settings.dashboard_dir, name)
        abort(404)

    @app.get("/test_forms/<path:name>")
    def test_form(name: str):
        if not name.endswith(".html"):
            abort(404)
        return send_from_directory(settings.test_forms_dir, name)

    @app.route("/test_forms/_submit", methods=["GET", "POST"])
    def fake_submit():
        # Practice forms post here. If this ever counts up during an agent run, that is a bug.
        app.config["SUBMIT_COUNT"] += 1
        return "This practice form was submitted. IntelliForm itself never does this.", 200

    @app.errorhandler(404)
    def not_found(_e):
        if request.path.startswith("/api/"):
            return error("not_found", "That API endpoint does not exist.", 404)
        return "Not found", 404

    @app.errorhandler(405)
    def bad_method(_e):
        return error("method_not_allowed", "That HTTP method is not allowed here.", 405)

    @app.errorhandler(413)
    def too_big(_e):
        return error("too_large", "The request was too large.", 413)

    @app.errorhandler(500)
    def server_error(_e):
        return error("internal_error", "Something went wrong on the server. See logs/intelliform.log.", 500)

    return app


def main() -> None:
    settings = Settings.from_env()
    setup_logging(settings)
    app = create_app(settings)
    print(f"IntelliForm is running. Open http://{settings.host}:{settings.port} in your browser.")
    print("Press Ctrl+C in this window to stop it.")
    # debug=False on purpose: the auto-reloader would start the agent twice.
    app.run(host=settings.host, port=settings.port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
