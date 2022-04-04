import os
import queue
import threading
import time
import flask
import logging

from typing import Callable, Any
from contextlib import contextmanager, suppress

from .port import PortSettings, ConfiguredPort


def forward_messages(
    flask_to_serial_Q: queue.Queue,
    serial_to_flask_Q: queue.Queue,
    settings: PortSettings,
    lockfile: str
):
    port = ConfiguredPort(settings)
    port.open()

    while True:
        try:
            incoming: bytes = flask_to_serial_Q.get(timeout=settings.f2sQ_timeout)
            if len(incoming):
                port.write(incoming)
        except queue.Empty as e:
            pass

        if port.in_waiting:
            outgoing: bytes = port.readline()
            serial_to_flask_Q.put(outgoing)

        if not os.path.exists(lockfile):
            break

    port.close()


class COM:
    def __init__(self, app: flask.Flask = None):
        self.portvar = 'FLASK_SERIAL_PORT_'
        self.forwarder: threading.Thread = None
        self.handler: threading.Thread = None
        self._on_message: dict[str, Callable[[str], Any]] = {}
        self._on_message_default: Callable[[str], Any] = None
        self.settings: PortSettings = None
        self._run_serial_queue_handler = False
        self.synchronous_mutex = threading.Lock()

        self._lockfile = '.flask_serial_running'

        self.serial_to_flask_Q = queue.Queue()
        self.flask_to_serial_Q = queue.Queue()

        if app is not None:
            self.init_app(app)


    def init_app(self, app: flask.Flask):
        # print('COM.init_app()')
        logging.info('COM.init_app()')
        self.settings = PortSettings.from_config_dict(app.config)
        self.portvar += self.settings.port
        self._lockfile = app.config.get('SERIAL_LOCK_FILE', self._lockfile)


    def run(self):
        # print('COM.run()')
        logging.info('COM.run()')
        self.forwarder = self.__start_forwarding_messages(self.settings)
        self.handler = self.__start_handling_serial_queue(self.settings)


    def __start_forwarding_messages(self, portSettings: PortSettings) -> threading.Thread:
        t = self.forwarder

        portenv = os.environ.get(self.portvar)
        if portenv is None:
            t = threading.Thread(
                target=forward_messages,
                args=(
                    self.flask_to_serial_Q,
                    self.serial_to_flask_Q,
                    portSettings,
                    self._lockfile,
                ),
                daemon=True
            )
            os.environ[self.portvar] = 'running'
            open(self._lockfile, 'w').close()

            t.start()
            self.forwarder = t
        else:
            del os.environ[self.portvar]

            with suppress(FileNotFoundError):
                os.remove(self._lockfile)

            time.sleep(0.1)

            return self.__start_forwarding_messages(portSettings)

        return t


    def __start_handling_serial_queue(self, portSettings: PortSettings) -> threading.Thread:
        self._run_serial_queue_handler = True

        def handle_serial_queue(serial_to_flask_Q: queue.Queue, is_running: Callable, settings: PortSettings):
            while is_running():
                try:
                    line: bytes = serial_to_flask_Q.get(block=False)
                except queue.Empty:
                    time.sleep(settings.f2sQ_sleep)
                else:
                    if len(line) > 0 and self._on_message is not None:
                        decoded = line.decode()
                        logging.debug(f'COM << {decoded}')

                        # TODO: Allow identifiers longer than 1 byte
                        # Instead of looking for the first byte in the keys
                        # It could search if any of the keys is in the received message
                        on_message = self._on_message.get(decoded[0], self._on_message_default)
                        if on_message:
                            on_message(decoded)


        t = threading.Thread(
            target=handle_serial_queue,
            args=(
                self.serial_to_flask_Q,
                lambda: self._run_serial_queue_handler,
                portSettings
            ),
            daemon=True
        )
        t.start()
        return t


    # TODO: Allow identifiers longer than 1 byte
    def on_message(self, first_byte: str = '') -> Callable[[Callable], Callable]:
        """serial receive message use decorator
        use：
            @com.on_message('#')
            def handle_message(msg):
                print(f"received message：{msg}")
        """
        def decorator(handler: Callable) -> Callable:
            if first_byte != '':
                self._on_message[first_byte] = handler
            else:
                self._on_message_default = handler
            return handler

        return decorator


    @property
    @contextmanager
    def synchronous(self):
        self.synchronous_mutex.acquire()

        self._run_serial_queue_handler = False
        self.handler.join()

        try:
            yield
        finally:
            self.handler = self.__start_handling_serial_queue(self.settings)
            self.synchronous_mutex.release()


    def read(self, blocking: bool = False) -> str:
        try:
            line: bytes = self.serial_to_flask_Q.get(
                timeout=self.settings.f2sQ_timeout if not blocking else None
            )
        except queue.Empty:
            line: bytes = b''

        decoded = line.decode()
        logging.debug(f'COM >> {decoded}')

        return decoded


    def blockingRead(self) -> str:
        return self.read(blocking=True)


    def write(self, msg: bytes) -> None:
        self.flask_to_serial_Q.put(msg)
