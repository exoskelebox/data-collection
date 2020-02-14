import sensors
import sys
import time
import glob


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


def calibrate_sensor(sensor_name):
    ports = find_sensors()
    sensors.reset_sensor_values(ports)
    
    calibration = ()
    
    for port in ports:
        # Placeholder
        if sensor_name == "calibration_closed" and port.name == "COM3":
            return sensors.calibrate_sensor(port)
        elif sensor_name == "calibration_open" and port.name == "COM4":
            return sensors.calibrate_sensor(port)
    print(calibration)


def check_os():
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    return ports


def find_sensors():
    ports = check_os()
    sensor_ports = sensors.find_serial_port(ports)
    return sensor_ports


# if __name__ == "__main__":
    # collect_data()
    # calibrate_sensors("COM4")
