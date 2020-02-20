from serial import Serial

class BIOX(Serial):
    def __init__(self, port, baudrate=9600, timeout=None, sensors=8):
        super().__init__(port=port, baudrate=baudrate, timeout=timeout)
        self.sensors = sensors
