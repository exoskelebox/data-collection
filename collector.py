from flask import Blueprint, render_template, flash, escape, redirect, url_for, request, send_from_directory, json, current_app, make_response
import os
from serial import Serial
from serial.tools import list_ports
from serial.tools.list_ports_common import ListPortInfo
import time
from biox import BIOX
import numpy as np
from serial.serialutil import SerialException
from typing import List
from concurrent.futures import Future, wait
from concurrent.futures.thread import ThreadPoolExecutor


collector = Blueprint('collector', __name__)


@collector.route('/calibration/<gesture>')
def calibration(gesture, **kwargs):
    device_name: str = gesture.split('_')[0].upper()

    if not device_name.isalpha():
        return make_response((f'"{device_name}" is not a valid device name', 400))

    port = get_biox_device_port(device_name)

    if not port:
        return make_response(('BIOX device not found, make sure it is connected and try again.', 500))

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
    ports = get_biox_device_ports()

    if not any(ports):
        return make_response(('A BIOX device was not found, make sure all devices are connected and try again.', 500))

    try:
        bioxes: List[BIOX] = []
        data = []

        for port in ports:
            num_sensors = next(device.get('num_sensors') for device in current_app.config.get(
                'BIOX_DEVICES').values() if port.serial_number in device.get('serial_number'))
            biox = BIOX(port.device, sensors=num_sensors)
            bioxes.append(biox)

        with ThreadPoolExecutor() as executor:
            t_end = time.time() + current_app.config.get('TEST_TIME', 5)
            while time.time() < t_end:
                data.append(
                    (list(executor.map(fetch_data, bioxes)), time.time()))

    except SerialException as err:
        return make_response(('BIOX device closed the connection prematurely', 500))
    else:
        return json.jsonify(data)
    finally:
        [biox.close() for biox in bioxes if biox]


def get_biox_device_port(key) -> ListPortInfo:
    """Gets the port of a biox device based on the serial number associated with key"""
    serial_number = str(current_app.config.get(key.upper()))
    port = next(port for port in list_ports.comports()
                if port.serial_number == serial_number)
    return port


def get_biox_device_ports() -> List[ListPortInfo]:
    """Gets the ports associated with a biox device"""
    return [port for port in list_ports.comports() if is_biox_device(port)]


def is_biox_device(port: ListPortInfo) -> bool:
    """Check if port is associated with a biox device"""
    return port.serial_number in [device.get('serial_number') for device in current_app.config.get('BIOX_DEVICES').values()]


def fetch_data(device: BIOX):
    device.fill_output_buffer()
    reading = device.readline()
    return reading
