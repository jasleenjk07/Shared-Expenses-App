import os

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from backend.config import Config
from backend.extensions import db, jwt
from backend.models import User
from backend.routes.auth import auth_bp
from backend.routes.expenses import expenses_bp
from backend.routes.groups import groups_bp
from backend.routes.import_routes import import_bp


def create_app(config_class=Config):
    app = Flask(__name__, static_folder=None)
    app.config.from_object(config_class)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    db.init_app(app)
    jwt.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(groups_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(import_bp)

    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok"})

    # Serve React build in production
    frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
    if os.path.isdir(frontend_dist):

        @app.route("/", defaults={"path": ""})
        @app.route("/<path:path>")
        def serve_frontend(path):
            if path and os.path.isfile(os.path.join(frontend_dist, path)):
                return send_from_directory(frontend_dist, path)
            return send_from_directory(frontend_dist, "index.html")

    with app.app_context():
        db.create_all()
        _seed_demo_user()

    return app


def _seed_demo_user():
    if not User.query.filter_by(email="demo@flatmates.app").first():
        user = User(email="demo@flatmates.app", name="Demo User")
        user.set_password("demo1234")
        db.session.add(user)
        db.session.commit()


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5001)))
else:
    app = create_app()
