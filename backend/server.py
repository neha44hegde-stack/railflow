"""API-only server. Serves /api/* only. Frontend runs separately on :5173."""
from app import create_app
from config import Config


class DevConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///railflow_dev.db"


app = create_app(DevConfig)


if __name__ == "__main__":
    # debug=False → no auto-reload scanning, much faster per request
    # threaded=True → handle concurrent requests
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)