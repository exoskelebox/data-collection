import sensors
import sys
import time
import glob
from serial.tools import list_ports
from serial import Serial
from serial.tools.list_ports_common import ListPortInfo
import serial
import os
from dotenv import load_dotenv
from array import array


def collect_data():
    ports = find_sensors()
    sensor_readings = []

    time_end = time.time() + 10

    while time.time() < time_end:
        port4_value, port3_value, time_unit = sensors.collect_sensor_data(
            ports)
        sensor_values = (port3_value, port4_value, time_unit)
        sensor_readings.append(sensor_values)

    return sensor_readings


def calibrate_sensor(gesture, **kwargs):
    device_name: str = gesture.split('_')[0].upper()
    port = get_biox_device_port(device_name)
    
    # settings
    num_sensors = 8
    offset = num_sensors - int(os.getenv(f'{device_name}:SENSORS', '8'))
    threshold = kwargs.get('threshold', 117)
    num_to_max = kwargs.get('num_to_max', 2)

    # initialize
    iterations = 0
    maxed_sensors = 0
    serial = None

    try:
        serial = Serial(port.device, baudrate=250000, bytesize=8, timeout=.01)
        
        while serial.readable():
            serial.write('S'.encode())
            reading = list(serial.readall()[offset:num_sensors])
            print(reading)
            maxed_sensors = len([i for i in reading if i > threshold])
            
            if maxed_sensors >= num_to_max:
                break
            else:
                serial.write('I'.encode())
                iterations += 1
    except Exception as ex:
        raise ex
    else:
        return reading, iterations
    finally:
        if (serial):
            serial.close()

def get_biox_device_port(key) -> ListPortInfo:
    """Gets the port of a biox device based on the serial number associated with key"""
    serial_number = os.getenv(key.upper())
    port = next(port for port in list_ports.comports() if port.serial_number == serial_number)
    return flush_biox_device(port)

def flush_biox_device(port):
    """Flush the biox device data"""
    serial = None
    try:
        serial = Serial(port.device, baudrate=250000, bytesize=8, timeout=1)
        serial.write("R".encode())
        serial.flush()
        serial.reset_input_buffer()
        serial.reset_output_buffer()
        time.sleep(.1)
        assert serial.out_waiting == 0, 'Serial device was not flushed properly'
    except Exception as ex:
        raise ex
    finally:
        if serial:
            serial.close()
        return port

def get_biox_device_ports() -> list:
    """Gets the ports associated with a biox device"""
    return [flush_biox_device(port) for port in list_ports.comports() if is_biox_device(port)]

def is_biox_device(port) -> bool:
    """Check if port is associated with a biox device"""
    serial = None
    try:
        serial = Serial(port.device, baudrate=250000, bytesize=8, timeout=1)
        serial.write('C'.encode())
        return True if 'A'.encode() in serial.read() else False
    except Exception as ex:
        return False
    finally:
        if serial:
            serial.close()

if __name__ == "__main__":
    load_dotenv()
    port = calibrate_sensor('wrist')
