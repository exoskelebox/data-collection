import sensors
import sys
import time
import glob
from serial.tools import list_ports
from serial import Serial

biox_devices = {
    'wrist': '4407090',
    'arm': '4083140'
}


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


def calibrate_sensor(gesture):
    ports = get_biox_device_ports()
    calibration = ()

    for port in ports:
        # Placeholder
        if gesture == "calibration_closed" and port.serial_number == biox_devices['arm']:
            return sensors.calibrate_sensor(port)
        elif gesture == "calibration_open" and port.serial_number == biox_devices['wrist']:
            return sensors.calibrate_sensor(port)


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


def flush_biox_device(port):
    """Flush the biox device data"""
    serial = None
    try:
        serial = Serial(port.device, baudrate=250000, bytesize=8, timeout=1)
        serial.write("R".encode())
        serial.flush()
        serial.flushInput()
        serial.flushOutput()
        # Without this, the buffer wont flush properly
        time.sleep(0.1)
    except Exception as ex:
        raise ex
    finally:
        if serial:
            serial.close()
        return port


if __name__ == "__main__":
    print(calibrate_sensor('calibration_open'))
