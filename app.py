import os
from flask import Flask, render_template
from frontend import frontend
from collector import collector
from filters import filters
from config import ProductionConfig, DevelopmentConfig

app = Flask(__name__, static_url_path='/static')

# Environment specific initializations
if app.config.get('FLASK_ENV', '') == 'development':
    app.config.from_object(DevelopmentConfig)
else:
    app.config.from_object(ProductionConfig)

app.register_blueprint(frontend)
app.register_blueprint(collector, url_prefix='/collect')
app.register_blueprint(filters)


@app.context_processor
def inject_debug():
    return dict(debug=app.debug)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
