import os
﻿from flask import Flask, jsonify
from config import Config
from extensions import db, jwt, cors


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {
            # RAILFLOW_RENDER_CORS
            "origins": [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                os.getenv("FRONTEND_URL", "https://railflow-frontend.onrender.com"),
            ],
            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
        }},
    )
    import models  # noqa

    from routes.auth import auth_bp
    from routes.stations import stations_bp
    from routes.trains import trains_bp
    from routes.search import search_bp
    from routes.bookings import bookings_bp
    from routes.pnr import pnr_bp
    from routes.admin import admin_bp

    for bp in (auth_bp, stations_bp, trains_bp, search_bp, bookings_bp, pnr_bp, admin_bp):
        app.register_blueprint(bp)

    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.errorhandler(404)
    def nf(_e): return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def se(_e): return jsonify({"error": "Server error"}), 500

    with app.app_context():
        db.create_all()
    return app


if __name__ == "__main__":
    import os as _os
    _port = int(_os.environ.get("PORT", 5000))
    create_app().run(host="0.0.0.0", port=_port, debug=False)

