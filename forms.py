import json
from flask_wtf import FlaskForm
from wtforms.widgets import HiddenInput, TextInput
from wtforms.fields import SelectField, IntegerField, SubmitField, StringField, Field, HiddenField, FloatField
from wtforms.validators import NumberRange, InputRequired

class JSONField(Field):
    def _value(self):
        return json.dumps(self.data) if self.data else ''

    def process_formdata(self, valuelist):
        if valuelist:
            try:
                self.data = json.loads(valuelist[0])
            except ValueError:
                self.data = {}
                raise ValueError('This field contains invalid JSON')
        else:
            self.data = None

    def pre_validate(self, form):
        super().pre_validate(form)
        if self.data:
            try:
                json.dumps(self.data)
            except TypeError:
                raise ValueError('This field contains invalid JSON')

class DataForm(FlaskForm):
    age = IntegerField(u'Age', validators=[InputRequired(), NumberRange(18,100)], render_kw={'um': 'years'})
    gender = SelectField(
        u'Gender', 
        choices=[('m', 'Male'), ('f', 'Female')], 
        validators=[InputRequired()]
    )
    phys_exercise = IntegerField(
        u'Physical exercise',
        description=u'The number of days per week you perform physical exercise for a minimum of 30 minutes (on average).',
        validators=[InputRequired(), NumberRange(0,7)],
        render_kw={'um': 'days'}
    )
    wrist_function = SelectField(
        u'Reduced wrist function',
        choices=[('n', 'No'), ('y', 'Yes')],
        description=u'Wether or not you have reduced right wrist functionality.',
        validators=[InputRequired()]
    )
    handedness = SelectField(
        u'Dominant hand',
        choices=[('r', 'Right'), ('l', 'Left'), ('a', 'Ambidextrous')],
        validators=[InputRequired()]
    )
    wrist_circumference = FloatField(u'Wrist circumference', validators=[InputRequired(), NumberRange(20,30)], render_kw={'um': 'cm'})
    arm_circumference = FloatField(u'Arm circumference', validators=[InputRequired(), NumberRange(25,40)], render_kw={'um': 'cm'})
    
    submit = SubmitField(u'Start test')

class CalibrateForm(FlaskForm):
    image = HiddenField(default='//:0')
    data = JSONField(widget=HiddenInput())

class TestForm(FlaskForm):
    identifier = HiddenField()
    image = HiddenField(default='//:0')
    data = JSONField(widget=HiddenInput())