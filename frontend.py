from flask import Blueprint, render_template, flash, escape, redirect, url_for, request, jsonify, send_from_directory
from flask import current_app as app
from .forms import DataForm
import time
import os
import random

frontend = Blueprint('frontend', __name__)

@frontend.route('/')
def index():
    return render_template('index.html')

@frontend.route('/form/', methods=('GET', 'POST'))
def data_form():
    form = DataForm()

    if form.validate_on_submit():
        return render_template('calibrate.html', form=form)
    return render_template('register.html', form=form)


@frontend.route('/gestures/sequence/<int:rep>')
def get_gesture_sequence(rep = 10, seed=42):
    gestures = os.listdir(os.path.join(app.static_folder, 'gestures'))
    sequences = [[gestures[(i+j) % len(gestures)] for i in range(len(gestures))] for j in range(rep) ]
    result = []

    for sequence in sequences:
        random.seed(seed)
        random.shuffle(sequence)
        result = result + sequence
    
    return jsonify(list(map(lambda x : app.static_url_path + '/gestures/' + x, result)))

@frontend.route('/calibrations/sequence')
def get_calibration_sequence():
    calibrations = os.listdir(os.path.join(app.static_folder, 'calibrations'))
    return jsonify(list(map(lambda x : app.static_url_path + '/calibrations/' + x, calibrations)))

@frontend.route('/collector/init')
def init_collector():
    return None

@frontend.route('/collector/calibrate')
def calibrate_collector():
    return None


@frontend.route('/collector/start')
def start_collector():
    # Placeholder: Call the data collection python function
    collected_data = [1, 2, 3]
    time.sleep(2)
    return jsonify(collected_data)

