from flask import Blueprint, current_app
from flask_socketio import SocketIO
from flask_serial import COM


arduino_bp = Blueprint('arduino', __name__)

com = COM(current_app)
socketio = SocketIO()


@com.on_message()
def handle_message(msg):
    print(f'handle_message: {msg}')
    socketio.emit('serial_message', data={'message': str(msg)})
