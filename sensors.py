from serial import Serial
import array
import datetime
import sys
import time
#from data_collection import biox_devices
# Testing stuff, remove when done
import data_collection as dc
from concurrent.futures.thread import ThreadPoolExecutor

NUM_SENSORS = 8
REPETITIONS = 10
DATA_SIZE = 80


biox_devices = {
    'wrist': '4407090',
    'arm': '4083140'
}



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
                        temp.pop(0)
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


def collect_sensor_data(devices):
    """Collects a data reading from the given sensor ports and returns lists for each wristband values and timestamp.

    >>> collect_sensor_data([]) is None
    True
    """

    wrist_data = []
    forearm_data = []
    t = time.time()

    data_stream = array.array('B')
    for port in devices:
        port[1].write('S'.encode())
        data_stream = array.array("B")
        data_stream.fromfile(port[1], DATA_SIZE)

        if port[0] == biox_devices['wrist']:
            # Sensor device with 7 FSR
            # ignore unused index as we only have 7 FSR and that value is not doing anything.
            wrist_data = data_stream[1:8]
        elif port[0] == biox_devices['arm']:
            # Sensor device with 8 FSR
            forearm_data = data_stream[:8]
        else:
            sys.stdout.write('ERROR: Collect_sensor_data: unknown device')

    return wrist_data, forearm_data, t

def csd_concurrent(devices, executor):
    tasks = [executor.submit(fetch_data, device) for device in devices]
    data = [task.result() for task in tasks]
    t = time.time()
    return data, t

def fetch_data(device):
    device[1].write('S'.encode())
    data_stream = array.array("B")
    data_stream.fromfile(device[1], DATA_SIZE)

    if device[0] == biox_devices['wrist']:
        # Sensor device with 7 FSR
        # ignore unused index as we only have 7 FSR and that value is not doing anything.
        return data_stream[1:8]
    elif device[0] == biox_devices['arm']:
        # Sensor device with 8 FSR
        return data_stream[:8]
    else:
        sys.stdout.write('ERROR: Collect_sensor_data: unknown device')


def test_concurrent_data_collection(devices, n=10**3):

    with ThreadPoolExecutor() as executor:
        counter = 0
        data = {}
        print(f"Collecting {n} data samples.")
        start_time = time.perf_counter()
        for i in range(n):
            if counter >= 100:
                print('.', end='', flush=True)
                counter = 0  
            data[i] = csd_concurrent(devices, executor)
            counter += 1
        print('\n')
    elapsed = time.perf_counter() - start_time
    print(f"Time: {n}\nElapsed: {elapsed}s\nFrequency: {n/elapsed}")
  


if __name__ == "__main__":
    devices = [(device.serial_number, Serial(device.device, baudrate=250000, bytesize=8, timeout=1)) for device in dc.get_biox_device_ports()]
    
    test_concurrent_data_collection(devices, n= 10**3)

    for serial_number, connection in devices:
            connection.write('D'.encode())





