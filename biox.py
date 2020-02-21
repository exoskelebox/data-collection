from serial import Serial
from time import sleep
import typing

class BIOX(Serial):
    def __init__(self, port, baudrate=256000, timeout=.003, sensors=8):
        super().__init__(port=port, baudrate=baudrate, timeout=timeout)
        self.sensors = sensors
        self.connect()
        self.calibration = Calibration(self)
        self.flush()

    def fill_output_buffer(self) -> None:
        """
        Write an "S" to the BIOX device which tells it to fill the output 
        buffer with lines.
        """
        self.write('S'.encode())

    def write(self, data) -> int:
        """
        Output the given string over the serial port.
        Wait specifies the amount of time in seconds to wait before returning,
        which is necessary before performing a read in most cases.
        """
        res = super().write(data)
        sleep(self.timeout)
        return res

    def read_all(self) -> bytes:
        """
        Read all bytes currently available in the buffer of the OS.
        """
        return super().read_all()

    def readline(self) -> typing.List[int]:
        """
        Read one line from the buffer of the OS.
        """
        line = list(super().read(8))
        return line[:self.sensors]
    
    def readlines(self) -> typing.List[typing.List[int]]:
        """
        Read all lines currently available in the buffer of the OS.
        """
        buffer = list(super().read_all()) 
        lines = [buffer[i:i+8] for i in range(0, len(buffer), 8)]
        return lines[:][:self.sensors]

    def connect(self) -> None:
        """
        Connect the BIOX device.
        """
        self.write('C'.encode())
        if 'A'.encode() not in self.read():
            raise IOError()

    def disconnect(self) -> None:
        """
        Disconnect the BIOX device. After doing so, 
        the device will remain passive until it is reconnected.
        """
        self.write("D".encode())

    def flush(self) -> None:
        """
        Flush the input and output buffer.
        """
        self.write("E".encode())
        super().flush()
        super().reset_input_buffer()
        super().reset_output_buffer()
        #sleep(self.timeout) # TODO: Flush validation is failing, there is still data in_waiting.
        if self.read() != ''.encode():
            raise ValueError('BIOX device flush failed')
        

    def close(self) -> None:
        """
        Close the port.
        """
        if self.is_open:
            self.flush()
            self.disconnect()
            return super().close()


class Calibration():
    def __init__(self, biox):
        self.biox: Serial = biox
        self.iterations = 0
        super().__init__()

    def increment(self) -> None:
        """
        Increment the sensors resting values.
        """
        self.biox.write('I'.encode())
        self.iterations += 1
    
    def decrement(self) -> None:
        """
        Decrement the sensors resting values.
        """
        self.biox.write('i'.encode())
        self.iterations -= 1

    def reset(self) -> None:
        """
        Reset the sensors resting values.
        """
        self.biox.write('R'.encode())
        self.iterations = 0
        self.biox.flush()