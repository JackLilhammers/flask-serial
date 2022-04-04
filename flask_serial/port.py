from serial import Serial
from typing import Any, Callable

from .PortSettings import PortSettings


class ConfiguredPort(Serial):

    def __init__(self, settings: PortSettings, **kwargs):
        super().__init__(
            # port     = settings.port,
            baudrate = settings.baudrate,
            bytesize = settings.bytesize,
            parity   = settings.parity,
            stopbits = settings.stopbits,
            timeout  = settings.timeout,
            **kwargs
        )
        self.port = settings.port


    def settings(self):
        return PortSettings(
            port     = self.port,
            baudrate = self.baudrate,
            bytesize = self.bytesize,
            parity   = self.parity,
            stopbits = self.stopbits,
            timeout  = self.timeout
        )
