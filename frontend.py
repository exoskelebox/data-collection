from flask import Blueprint, render_template, flash, escape, redirect, url_for, request, send_from_directory
import flask.json as json
from flask import current_app as app
from forms import DataForm, CalibrateForm, TestForm
from filters import is_hidden_field, is_submit_field
import time
import os
import random
import csv
import uuid
import math
import database

frontend = Blueprint('frontend', __name__)
data_folder = 'data'


def ensure_folder_exists(folder):
    '''Creates the folder if it does not exist, 
    or throws an error if the path is a file'''
    if not os.path.exists(folder):
        os.mkdir(folder)
    elif not os.path.isdir(folder):
        raise FileExistsError()


@frontend.route('/')
def index():
    return render_template('index.html')

@frontend.route('/thank-you')
def done():
    return render_template('complete.html')

@frontend.route('/form/', methods=('GET', 'POST'))
def data_form():
    form = DataForm()

    if form.validate_on_submit():

        # construct subject tuple
        subject = tuple(field.data for field in form if not (is_hidden_field(field) or is_submit_field(field)))
        # attempt to insert into database
        try:
            user_id = database.insert_subject(subject)
        except Exception as identifier:
            print(identifier)
            flash('Could not insert into database, please check the fields and try again.', 'danger')
        else:
            return redirect(url_for('.calibrate', user_identifier=user_id, step=0))

        
    return render_template('form.html', form=form)


@frontend.route('/calibrate/<int:user_id>/<int:step>', methods=('GET', 'POST'))
def calibrate(user_id, step):
    form = CalibrateForm()
    calibration_image_urls = get_calibration_sequence()
    data = form.data.data
    gesture = form.image.data

    # Handle index out of range error
    if step >= len(calibration_image_urls):
        return redirect(url_for('.calibrate', user_id=user_id, step=len(calibration_image_urls) - 1))

    # TODO: remove existing data if any from database

    if form.validate_on_submit():
        # TODO: write to database
        print(data)

        if step == len(calibration_image_urls) - 1:
            return redirect(url_for('.test', test_identifier=str(uuid.uuid4()), step=0))
        else:
            return redirect(url_for('.calibrate', user_id=user_id, step=step + 1))

    form.image.data = calibration_image_urls[step]
    gesture = form.image.data.split('/')[-1].split('.')[0]
    form.data.data = None
    status_text = f'Calibration: {int(step % len(calibration_image_urls)) + 1} / {len(calibration_image_urls)}'
    return render_template('calibrate.html', form=form, status=status_text, gesture=gesture)


@frontend.route('/test/<test_identifier>/<calibration_identifier>/<int:step>', methods=('GET', 'POST'))
def test(test_identifier, calibration_identifier, step, reps=5):
    form = TestForm()
    test_image_urls = get_gesture_sequence(reps)
    data = form.data.data
    gesture = form.image.data

    # Handle index out of range error
    if step >= len(test_image_urls):
        return redirect(url_for('.test', calibration_identifier=calibration_identifier, step=len(test_image_urls) - 1))

    # TODO: remove data with matching id, cal_id && gesture from database

    if form.validate_on_submit():
        ensure_folder_exists(data_folder)

        row = {
            'id': test_identifier,
            'cal_id': calibration_identifier,
            'gesture': gesture
        }

        with open(f'{data_folder}/{calibration_identifier}.csv', 'a+') as f:
            # TODO: insert data into database
            for reading_1, reading_2, timestamp in data:
                row['reading_1'] = reading_1
                row['reading_2'] = reading_2
                row['timestamp'] = timestamp

                w = csv.DictWriter(f, row.keys())
                w.writeheader()
                w.writerow(row)

        if step == len(test_image_urls) - 1:
            return redirect(url_for('.done'))
        else:
            return redirect(url_for('.test', test_identifier=test_identifier, calibration_identifier=calibration_identifier, step=step + 1))

    form.image.data = test_image_urls[step]
    form.data.data = None
    tests_per_rep = int(len(test_image_urls) / reps)
    status_text = f'''Test: {int(step % tests_per_rep) + 1} / {tests_per_rep}
        Rep: {math.ceil((step + 1) / tests_per_rep)} / {reps}'''
    return render_template('test.html', form=form, status=status_text)


def get_gesture_sequence(rep=10, seed=42):
    gestures = os.listdir(os.path.join(app.static_folder, 'gestures'))
    sequences = [[gestures[(i+j) % len(gestures)]
                  for i in range(len(gestures))] for j in range(rep)]
    result = []

    for sequence in sequences:
        random.seed(seed)
        random.shuffle(sequence)
        result = result + sequence

    return list(map(lambda x: app.static_url_path + '/gestures/' + x, result))


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
