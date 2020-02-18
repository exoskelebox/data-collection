from serial import Serial
import array
from datetime import datetime
import sys
import time
from data_collection import biox_devices

# OBSOLETE
""" def find_serial_port(ports):
    find_ports = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            find_ports.append(port)
        except (OSError, serial.SerialException):
            pass
    i = 0
    serial_devices = []

    if len(find_ports) != 0:
        while i < len(find_ports):
            get_Serial = serial.Serial(
                find_ports[i], baudrate=250000, bytesize=8)
            get_Serial.write('C'.encode())
            Receive_data = get_Serial.read()
            if 'A'.encode() in Receive_data:
                print("Device found")
                serial_devices.append(get_Serial)
                i += 1
            else:
                print("Device not found")
                get_Serial.close()
                i += 1
    return serial_devices """


def reset_sensor_values(ports):
    if len(ports) == 1:
        ports[0].write("R".encode())
    else:
        for port in ports:
            port.write("R".encode())
            port.flush()
            port.flushInput()
            port.flushOutput()
            # Without this, the buffer wont flush properly
            time.sleep(0.1)
            print(f'Port: {port.name} has been reset')

def test_sensor_calibration(ports, num_to_max=1):
    sensors_amount = 8
    repetition = 10
    data_size = sensors_amount * repetition
    threshold = 117
    no_inc = False
    while True:
        ports[0].write('S'.encode())
        data_stream = array.array('B')
        data_stream.fromfile(ports[0], data_size)
        i = 0
        while i < len(data_stream):
            j = i
            temp = []

            while j < (i+sensors_amount):
                j += 1
                temp.append(data_stream[len(data_stream) - j])
            temp.pop(6)
            i += sensors_amount
            # Takes only the elements whose value is > threshold
            maxed_sensors = len([i for i in temp if i > threshold])
            if maxed_sensors >= num_to_max:
                no_inc = True
            #    break
        # 'I' increases the sensitivity of the sensors
        if not no_inc:
            ports[0].write('I'.encode())
        else:
            print(temp)


def calibrate_sensor(port, num_to_max=2):
    sensors_amount = 8
    repetition = 10
    data_size = sensors_amount * repetition
    threshold = 117
    iteration_count = 0
    sensor_raw_data = []

    serial = None
    try:
        serial = Serial(port.device, baudrate=250000, bytesize=8, timeout=1)
        serial.write('S'.encode())
        data_stream = array.array('B')
        data_stream.fromfile(serial, data_size)
        maxed_sensors = 0
        while maxed_sensors < num_to_max:
            # 'S' receives a data reading from the sensor
            serial.write('S'.encode())
            data_stream = array.array('B')
            data_stream.fromfile(serial, data_size)
            i = 0
            while i < len(data_stream):
                j = i
                temp = []

                while j < (i+sensors_amount):
                    j += 1
                    temp.append(data_stream[len(data_stream) - j])
                i += sensors_amount
                # Takes only the elements whose value is > threshold
                maxed_sensors = len([i for i in temp if i > threshold])

                if maxed_sensors >= num_to_max:
                    if port.serial_number == biox_devices['wrist']:
                        temp.pop(1)
                        sensor_raw_data = temp
                    else:
                        sensor_raw_data = temp
                    break
                serial.write('I'.encode())
                time.sleep(0.01)
                iteration_count += 1
        return (sensor_raw_data, iteration_count)

    except Exception as ex:
        raise ex
    finally:
        if serial:
            serial.close()


def collect_sensor_data(ports):
    """Collects 10 data readings from the given sensor ports and returns lists for each wristband values and timestamp.

    >>> collect_sensor_data([]) is None
    True
    """
    if not len(ports) > 0:
        return None

    sensors_amount = 8
    repetition = 10
    # How many readings for each sensor do we want to receive from the device
    data_size = sensors_amount * repetition
    data_com3 = []
    data_com4 = []
    t = datetime.utcnow().timestamp()
    time = [t for _ in range(repetition)]

    for port in ports:
        port.write('S'.encode())
        data_stream = array.array("B")
        data_stream.fromfile(port, data_size)
        i = 1
        l = len(data_stream)
        j = 1
        while i <= l:
            j += sensors_amount
            temp = []
            while i < j:
                temp.append(data_stream[l - i])
                i += 1
            # We assume that the device COM4 has the arm band with 7 sensors.

            if port.name == "COM4":
                # Sensor device with 7 FSR
                # Pop index 1 as we only have 7 FSR and that value is not doing anything.
                temp.pop(6)
                data_com4.append(temp)
            elif port.name == "COM3":
                # Sensor device with 8 FSR
                data_com3.append(temp)
            else:
                sys.stdout.write('ERROR: Collect_sensor_data: unknown device')
    return data_com4, data_com3, time
