import os

###############################################################
# Attenzione!
# Carico le variabili d'ambiente il prima possibile
# Gli import delle nostre librerie vanno sotto
from dotenv import load_dotenv
load_dotenv()
###############################################################

from flask import Flask, Blueprint

import appdirs

# Routes
def register_blueprints(app: Flask, blueprints: list[Blueprint]):
    for bp in blueprints:
        app.register_blueprint(bp)


def create_app() -> Flask:
    app = Flask(__name__)

    app.config['SERIAL_TIMEOUT']  = 0.1
    app.config['SERIAL_PORT']     = os.environ['ARDUINO_PORT']
    app.config['SERIAL_BAUDRATE'] = 9600
    app.config['SERIAL_BYTESIZE'] = 8
    app.config['SERIAL_PARITY']   = 'N'
    app.config['SERIAL_STOPBITS'] = 1

    serial_lock_file = f"{appdirs.user_data_dir(appname='flask_arduino', appauthor='flask_serial')}/running"
    app.config['SERIAL_LOCK_FILE'] = serial_lock_file

    with app.app_context():
        from .routes import (
            arduino_bp
        )

    app.register_blueprint(arduino_bp)

    return app


# If run directly
def main():
    app = create_app()
    debug_enabled = os.environ.get("DEBUG", 'False').lower() == 'true'

    # DO NOT MOVE!
    # Moving this import crashes the program!
    from app.routes.arduino import com, socketio

    com.run()

    socketio.init_app(app, cors_allowed_origins="*")
    socketio.run(app, port=8888, host='0.0.0.0', debug=debug_enabled, use_reloader=debug_enabled)


if __name__ == "__main__":
    main()
