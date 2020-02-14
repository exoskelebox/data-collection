import os
from flask import Flask, render_template
from frontend import frontend
from filters import filters

app = Flask(__name__, static_url_path='/static')
app.register_blueprint(frontend)
app.register_blueprint(filters)
app.config['SECRET_KEY'] = os.urandom(32)

@app.context_processor
def inject_debug():
    return dict(debug=app.debug)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404