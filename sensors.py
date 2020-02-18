from serial import Serial
import array
import datetime
import sys
import time
from data_collection import biox_devices
import timeit



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


def old_collect_sensor_data(ports, data_stream):
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
    wrist_data = []
    forearm_data = []

    t = datetime.datetime.utcnow()


    for port in ports:
        #port.write('S'.encode())
        stream = array.array("B")
        #data_stream.fromfile(port, data_size)
        i = 1
        temp = []

        while i < len(data_stream):
            j = i + sensors_amount
            while i < j:
                i += 1
                temp.append(data_stream[len(data_stream) - i])
            
        if port == "COM4":
            # Sensor device with 7 FSR
            # Pop index 1 as we only have 7 FSR and that value is not doing anything.
            temp.pop(6)
            wrist_data = temp
        elif port == "COM3":
            # Sensor device with 8 FSR
            forearm_data = temp
        else:
            sys.stdout.write('ERROR: Collect_sensor_data: unknown device')
    return wrist_data, forearm_data, t


def collect_sensor_data(ports, data_stream):
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
    wrist_data = []
    forearm_data = []

    t = time.time()

    for port in ports:
        #port.write('S'.encode())
        stream = array.array("B")
        #data_stream.fromfile(port, data_size)

        temp = data_stream[:9]
        
        if port == "COM4":
            # Sensor device with 7 FSR
            # Pop index 1 as we only have 7 FSR and that value is not doing anything.
            temp.pop(6)
            wrist_data = temp
        elif port == "COM3":
            # Sensor device with 8 FSR
            forearm_data = temp
        else:
            sys.stdout.write('ERROR: Collect_sensor_data: unknown device')
    return wrist_data, forearm_data, t

if __name__ == "__main__":
    ports = ['COM3', 'COM4']
    
    la = [
        'collect_sensor_data(ports, data)',
        'old_collect_sensor_data(ports, data)',
    ]

    n = 10**6

    for l in la:
        break
        elapsed = timeit.timeit(
            l, 
            setup='import array, time, datetime, random;' 
                'from __main__ import collect_sensor_data, old_collect_sensor_data;'
                'data = array.array("B", [random.randint(5, 155) for _ in range(80)]);'
                'ports = ["COM3", "COM4"];', 
            number=n)
        print(f"{l:30}: {elapsed:20}s = 1M * {(elapsed/n)*1000000}us ")
