import eventlet
eventlet.monkey_patch()

import os

from eventlet.green import threading
from eventlet.green import time

# import threading
# import time
import multiprocessing as mp

from serial import Serial

from aioserial_ import async_port, thread_port, green_port

from flask import Flask, render_template
from flask_serial import PortSettings
from flask_socketio import SocketIO
from flask_bootstrap import Bootstrap



port = PortSettings(
    port     = 'COM5',
    timeout  = 0.1,
    baudrate = 9600,
    bytesize = 8,
    parity   = 'N',
    stopbits = 1
)

app = Flask(__name__)

app.config.from_mapping(**port.to_config_dict())


# socketio = SocketIO(app, async_mode='threading')
# socketio = SocketIO(app, async_mode='eventlet')
socketio = SocketIO(app)
bootstrap = Bootstrap(app)


@app.route('/')
def index():
    return render_template('index.html')

class ProcessSerial(object):

    def __init__(self, settings: PortSettings):
        self.settings = settings
        self.serial = Serial()

    def connect(self):
        self.serial.port     = self.settings.port
        self.serial.timeout  = self.settings.timeout
        self.serial.baudrate = self.settings.baudrate
        self.serial.bytesize = self.settings.bytesize
        self.serial.parity   = self.settings.parity
        self.serial.stopbits = self.settings.stopbits
        self.serial.open()


def async_listener(q: mp.Queue):
    line = bytearray()
    while True:
        byte: str = queue.get()
        if byte != '\n':
            line.extend(byte.encode())
        else:
            print(line.decode())
            line.clear()
            # socketio.emit("serial_message", data={"message":str(line)})


def thread_listener(q: mp.Queue):
    while True:
        line: bytes = queue.get()
        if len(line) > 0:
            print(line.decode())
            # socketio.emit("serial_message", data={"message":str(line)})


def green_listener(q: mp.Queue):
    while True:
        if q.empty():
            eventlet.greenthread.sleep(0.1)
        else:
            line: bytes = q.get()
            if len(line) > 0:
                print(line.decode())
                # socketio.emit("serial_message", data={"message":str(line)})

if __name__ == '__main__':
    queue = mp.Queue()

    # p = mp.Process(target=async_port, args=(queue, port,))
    portvar = f'LABO_SERIAL_PORT_' + port.port
    portenv = os.environ.get(portvar)
    print(portenv)
    if os.environ.get(portvar) is None:
        os.environ[portvar] = portvar
        # p = mp.Process(target=thread_port, args=(queue, port,))
        p = mp.Process(target=green_port, args=(queue, port,))
        p.start()
    portenv = os.environ.get(portvar)
    print(portenv)

    # t = threading.Thread(target=async_listener, args=(queue,), daemon=True)
    # t.start()
    # t = threading.Thread(target=thread_listener, args=(queue,), daemon=True)
    # t.start()
    t = eventlet.spawn(green_listener, queue)

    socketio.run(app, debug=False)

    # Wait for the worker to finish
    queue.close()
    queue.join_thread()
    p.join()