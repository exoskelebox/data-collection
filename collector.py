from flask import Blueprint, render_template, flash, escape, redirect, url_for, request, send_from_directory, json, current_app, make_response
import os
from serial import Serial
from serial.tools import list_ports
from serial.tools.list_ports_common import ListPortInfo
import time
from biox import BIOX
import numpy as np
from serial.serialutil import SerialException


collector = Blueprint('collector', __name__)


@collector.route('/calibration/<gesture>')
def calibration(gesture, **kwargs):
    device_name: str = gesture.split('_')[0].upper()

    if not device_name.isalpha():
        return make_response((f'"{device_name}" is not a valid device name', 400))

    port = get_biox_device_port(device_name)

    if not port:
        return make_response(('BIOX device not found, make sure it is connected and try again.', 500))

    print(port)
    # settings
    num_sensors = current_app.config.get(f'{device_name}_sensors'.upper(), 8)
    threshold = kwargs.get('threshold', 117)
    num_to_max = kwargs.get('num_to_max', 2)

    # initialize
    maxed_sensors = 0

    try:
        biox = BIOX(port.device, sensors=num_sensors)
        biox.calibration.reset()
        while biox.readable():
            biox.fill_output_buffer()
            reading = biox.readline()
            biox.flush()
            maxed_sensors = len([i for i in reading if i > threshold])
            if maxed_sensors >= num_to_max:
                break
            else:
                biox.calibration.increment()
    except SerialException as err:
        return make_response(('BIOX device closed the connection prematurely', 500))
    else:
        biox.close()
        return json.jsonify((reading, biox.calibration.iterations))


@collector.route('data/')
def data():
    return json.jsonify(None)


def get_biox_device_port(key) -> ListPortInfo:
    """Gets the port of a biox device based on the serial number associated with key"""
    serial_number = str(current_app.config.get(key.upper()))
    port = next(port for port in list_ports.comports()
                if port.serial_number == serial_number)
    return port


def flush_biox_device(port):
    """Flush the biox device data"""
    serial = None
    try:
        serial = Serial(port.device, baudrate=250000, bytesize=8, timeout=1)
        serial.write("R".encode())
        time.sleep(.1)
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
    device_name: str = 'arm'.upper()
    serial_number = '4083140' # '4407090'
    port: ListPortInfo = next(port for port in list_ports.comports() if port.serial_number == serial_number)
    # settings
    num_sensors = 7
    threshold = 117
    num_to_max = 2

    # initialize
    iterations = 0
    maxed_sensors = 0

    with BIOX(port.device, sensors=num_sensors) as biox:
        biox.calibration.reset()
        while biox.readable():
            biox.fill_output_buffer()
            reading = biox.readline()
            print(reading)
            biox.flush()
            maxed_sensors = len([i for i in reading if i > threshold])
            if maxed_sensors >= num_to_max:
                break
            else:
                biox.calibration.increment()
                iterations += 1