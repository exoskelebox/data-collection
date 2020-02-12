import os
from flask import Flask
from frontend import frontend
from filters import filters

app = Flask(__name__, static_url_path='/static')
app.register_blueprint(frontend)
app.register_blueprint(filters)
app.config['SECRET_KEY'] = os.urandom(32)

@app.context_processor
def inject_debug():
    return dict(debug=app.debug)