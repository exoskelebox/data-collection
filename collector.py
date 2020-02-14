from flask import Blueprint, render_template, flash, escape, redirect, url_for, request, send_from_directory, json

collector = Blueprint('collector', __name__)

@collector.route('/calibration/<gesture>')
def calibration(gesture):
    return json.jsonify([gesture, (50, 30, 1242134), (30, 40, 234234), (23, 45, 234234)])
