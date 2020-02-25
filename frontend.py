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
import database as db

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
        subject = {
            'subject_age': form.age,
            'subject_gender': form.gender,
            'subject_fitness': form.phys_exercise,
            'subject_impairment': form.wrist_function,
            'subject_handedness': form.handedness,
            'subject_wrist_circumference': form.wrist_circumference,
            'subject_forearm_circumference': form.arm_circumference,
        }
        # attempt to insert into database
        try:
            user_id = db.insert_subject(subject)
        except Exception as identifier:
            flash(
                'Could not insert into database, please check the fields and try again.', 'danger')
        else:
            return redirect(url_for('.calibrate', user_id=user_id, step=0))

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

        # construct calibration tuple
        calibration_values, calibration_iterations = data
        calibration = {
            'subject_id': user_id,
            'calibration_gesture': gesture,
            'calibration_values': calibration_values,
            'calibration_iterations': calibration_iterations
        }
        # attempt to insert into database
        try:
            db.insert_calibration(calibration)
        except Exception as identifier:
            flash(
                'Could not insert into database, please check the fields and try again.', 'danger')
        else:
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
    
    tests_per_rep = int(len(test_image_urls) / reps)
    rep = math.ceil((step + 1) / tests_per_rep)
    
    # remove data with matching id, cal_id && gesture from database
    db.clear_existing_data({
                'subject_id': test_identifier,
                'gesture': gesture,
                'repetition': rep})

    if form.validate_on_submit():
        # insert data into database
        count = 0
        for reading, time in data:
            reading_1, reading_2 = reading
            readings = reading_1 + reading_2
            timestamp = time.strftime("%H:%M:%S.{}".format(repr(time.time()).split('.')[1]), time.localtime(time.time()))

            data.append({
                'subject_id': test_identifier,
                'gesture': gesture,
                'repetition': rep,
                'reading_count': count,
                'readings': readings,
                'timestamp': timestamp
            })
            count += 1
            # attempt to insert into database
        try:
            db.insert_data_repetition(data)
        except Exception as identifier:
            flash('Could not insert into database, please check the fields and try again.', 'danger')
        
        if step == len(test_image_urls) - 1:
            return redirect(url_for('.done'))
        else:
            return redirect(url_for('.test', test_identifier=test_identifier, calibration_identifier=calibration_identifier, step=step + 1))

    form.image.data = test_image_urls[step]
    form.data.data = None
    status_text = f'''Test: {int(step % tests_per_rep) + 1} / {tests_per_rep}
        Rep: {rep} / {reps}'''
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
