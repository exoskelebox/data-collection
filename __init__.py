import os
from flask import Flask
#from flask_bootstrap import Bootstrap
from .frontend import frontend
from .filters import filters


def create_app():
    app = Flask(__name__, static_url_path='/static')
    app.register_blueprint(frontend)
    app.register_blueprint(filters)
    app.config['BOOTSTRAP_SERVE_LOCAL'] = True
    app.config['SECRET_KEY'] = os.urandom(32)
    return app