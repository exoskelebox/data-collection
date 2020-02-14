from flask import Blueprint, render_template, flash, escape, redirect, url_for, request, send_from_directory, json
from data_collection import collect_data, calibrate_sensor
collector = Blueprint('collector', __name__)

@collector.route('/calibration/<gesture>')
def calibration(gesture):
    return json.jsonify(calibrate_sensor(gesture))

@collector.route('data/')
def data():
    return json.jsonify(collect_data())

