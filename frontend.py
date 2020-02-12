from flask import Blueprint, render_template, flash, escape, redirect, url_for, request, send_from_directory
import flask.json as json
from flask import current_app as app
from .forms import DataForm, CalibrateForm
from .filters import is_hidden_field, is_submit_field
import time
import os
import random
import csv
import uuid

frontend = Blueprint('frontend', __name__)
data_folder = 'data'


def ensure_folder_exists(folder):
    '''Creates the folder if it does not exist, 
    or throws an error if the path is a file'''
    if not os.path.exists(folder):
        os.mkdir(folder)
    elif not os.path.isdir(folder):
        raise FileExistsError()

def ensure_deleted(path):
    


@frontend.route('/')
def index():
    return render_template('index.html')


@frontend.route('/form/', methods=('GET', 'POST'))
def data_form():
    form = DataForm()

    if form.validate_on_submit():

        row = {}

        # Add a row identifier for pairing with calibration and test data
        row['id'] = str(uuid.uuid4())

        # Add the form data to the row
        for field in form:
            if is_hidden_field(field) or is_submit_field(field):
                continue
            row[field.name] = field.data

        # Ensure the data folder exists before we attempt to save data
        ensure_folder_exists(data_folder)

        # Save the form data dictionary to a csv file in the data folder
        with open(f'{data_folder}/userdata.csv', 'a+') as f:
            w = csv.DictWriter(f, row.keys())
            w.writeheader()
            w.writerow(row)

        return redirect(url_for('frontend.calibrate', id=row['id']))
    return render_template('register.html', form=form)


@frontend.route('/calibrate/<user_identifier>', methods=('GET', 'POST'))
def calibrate(user_identifier):
    form = CalibrateForm()
    step = form.step.data

    if step == 0:
        form.identifier.data = str(uuid.uuid4())

    identifier = form.identifier.data
    data = form.data.data
    gesture = form.image.data

    if form.validate_on_submit():
        ensure_folder_exists(data_folder)

        row = {
            'id': identifier,
            'user_id': user_identifier,
            'gesture': gesture
        }

        with open(f'{data_folder}/{user_identifier}.csv', 'a+') as f:
            for reading_1, reading_2, timestamp in data:
                row['reading_1'] = reading_1
                row['reading_2'] = reading_2
                row['timestamp'] = timestamp

                w = csv.DictWriter(f, row.keys())
                w.writeheader()
                w.writerow(row)

        form.step.data += 1

    step = form.step.data
    calibration_image_urls = get_calibration_sequence()
    form.image.data = calibration_image_urls[step]
    form.data.data = None
    return render_template('calibrate.html', form=form)


@frontend.route('/gestures/sequence/<int:rep>')
def get_gesture_sequence(rep=10, seed=42):
    gestures = os.listdir(os.path.join(app.static_folder, 'gestures'))
    sequences = [[gestures[(i+j) % len(gestures)]
                  for i in range(len(gestures))] for j in range(rep)]
    result = []

    for sequence in sequences:
        random.seed(seed)
        random.shuffle(sequence)
        result = result + sequence

    return json.jsonify(list(map(lambda x: app.static_url_path + '/gestures/' + x, result)))


""" @frontend.route('/calibrations/sequence')
def get_calibration_sequence():
    calibrations = os.listdir(os.path.join(app.static_folder, 'calibrations'))
    return jsonify(list(map(lambda x: app.static_url_path + '/calibrations/' + x, calibrations)))
 """


def get_calibration_sequence():
    calibrations = os.listdir(os.path.join(app.static_folder, 'calibrations'))
    return list(map(lambda x: app.static_url_path + '/calibrations/' + x, calibrations))


@frontend.route('/collector/init')
def init_collector():
    return None


@frontend.route('/collector/calibrate')
def calibrate_collector():
    return None


@frontend.route('/collector/start')
def start_collector():
    # Placeholder: Call the data collection python function
    collected_data = {}
    collected_data['reader_1'] = [50, 30, 23]
    collected_data['reader_2'] = [50, 30, 23]
    collected_data['timestamps'] = [12312342134, 2134123253, 21341324213]

    time.sleep(2)
    return json.jsonify([(50, 30, 1242134), (30, 40, 234234), (23, 45, 234234)])
