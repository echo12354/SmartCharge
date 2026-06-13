"""Flask application entry for the redesigned charging station backend."""

from flask import Flask

try:
    from flask_cors import CORS
except ImportError:  # CORS is optional for the first backend-only version.
    CORS = None

from controllers.acceptance_controller import acceptance_bp
from controllers.auth_controller import auth_bp
from controllers.bill_controller import bill_bp
from controllers.charging_request_controller import charging_request_bp
from controllers.charging_session_controller import charging_session_bp
from controllers.compatibility_controller import compat_bp
from controllers.fault_controller import fault_bp
from controllers.pile_controller import pile_bp
from controllers.queue_controller import queue_bp
from controllers.scheduling_controller import scheduling_bp
from database.db import get_database_status
from config.settings import SIMULATION_ENABLED
from utils.responses import success
from utils.sim_clock import sim_clock


def create_app():
    app = Flask(__name__)
    if CORS:
        CORS(app)

    if not SIMULATION_ENABLED:
        sim_clock.disable()

    app.register_blueprint(acceptance_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(compat_bp)
    app.register_blueprint(charging_request_bp)
    app.register_blueprint(queue_bp)
    app.register_blueprint(scheduling_bp)
    app.register_blueprint(charging_session_bp)
    app.register_blueprint(bill_bp)
    app.register_blueprint(pile_bp)
    app.register_blueprint(fault_bp)

    @app.get("/api/health")
    def health():
        return success("charging station backend is running", {"database": get_database_status()})

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
