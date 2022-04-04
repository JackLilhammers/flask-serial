import serial

from dataclasses import dataclass


# timeout = None: wait forever / until requested number of bytes are received
# timeout = 0:    non-blocking mode, return immediately in any case, returning zero or more, up to the requested number of bytes
# timeout = x:    set timeout to x seconds (float allowed) returns immediately when the requested number of bytes are available, otherwise wait until the timeout expires and return all bytes that were received until then.

@dataclass
class PortSettings:
    port:          str
    baudrate:      int   = None # Default 9600
    bytesize:      int   = serial.EIGHTBITS
    parity:        str   = serial.PARITY_NONE
    stopbits:      int   = serial.STOPBITS_ONE
    timeout:       float = None # Blocking
    f2sQ_timeout:  float = 0.1  # 100 ms
    f2sQ_sleep:    float = 0.01 #  10 ms


    # Settings names to be used as dictionary keys
    PORT          = 'SERIAL_PORT'
    BAUDRATE      = 'SERIAL_BAUDRATE'
    BYTESIZE      = 'SERIAL_BYTESIZE'
    PARITY        = 'SERIAL_PARITY'
    STOPBITS      = 'SERIAL_STOPBITS'
    TIMEOUT       = 'SERIAL_TIMEOUT'
    F2SQ_TIMEOUT  = 'SERIAL_F2SQ_TIMEOUT'
    F2SQ_SLEEP    = 'SERIAL_F2SQ_SLEEP'


    def __post_init__(self):
        if self.baudrate is None:
            print("Serial port baudrate is not configured. Defaulting to 9600 kbps")
            self.baudrate = 9600

        if self.timeout is None:
            print("Serial port timeout is not configured. Calls to read() are blocking")


    def to_config_dict(self):
        return {
            PortSettings.PORT         : self.port,
            PortSettings.BAUDRATE     : self.baudrate,
            PortSettings.BYTESIZE     : self.bytesize,
            PortSettings.PARITY       : self.parity,
            PortSettings.STOPBITS     : self.stopbits,
            PortSettings.TIMEOUT      : self.timeout,
            PortSettings.F2SQ_TIMEOUT : self.f2sQ_timeout,
            PortSettings.F2SQ_SLEEP   : self.f2sQ_sleep
        }


    @classmethod
    def from_config_dict(cls, config: dict):
        settings: PortSettings = cls(
            port         = config.get(PortSettings.PORT),
            baudrate     = config.get(PortSettings.BAUDRATE,     PortSettings.baudrate),
            bytesize     = config.get(PortSettings.BYTESIZE,     PortSettings.bytesize),
            parity       = config.get(PortSettings.PARITY,       PortSettings.parity),
            stopbits     = config.get(PortSettings.STOPBITS,     PortSettings.stopbits),
            timeout      = config.get(PortSettings.TIMEOUT,      PortSettings.timeout),
            f2sQ_timeout = config.get(PortSettings.F2SQ_TIMEOUT, PortSettings.f2sQ_timeout),
            f2sQ_sleep   = config.get(PortSettings.F2SQ_SLEEP,   PortSettings.f2sQ_sleep)
        )
        if settings.port is None:
            raise IOError("Serial port name is not configured!")

        return settings
