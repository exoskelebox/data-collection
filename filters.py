from flask import Blueprint
from wtforms.fields import HiddenField, SubmitField

filters = Blueprint('filters', __name__)

@filters.app_template_filter('is_hidden_field')
def is_hidden_field(field):
    return isinstance(field, HiddenField)

@filters.app_template_filter('is_submit_field')
def is_submit_field(field):
    return isinstance(field, SubmitField)

@filters.app_template_filter('has_um')
def has_um(field):
    """
        Check if field render keywords contain a unit of measurement
    """
    return True if field.render_kw and 'um' in field.render_kw else False