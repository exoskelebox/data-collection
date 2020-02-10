from flask_wtf import FlaskForm
from wtforms.fields import SelectField, IntegerField, SubmitField
from wtforms.validators import NumberRange, InputRequired


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
    wrist_circumference = IntegerField(u'Wrist circumference', validators=[InputRequired(), NumberRange(10,20)], render_kw={'um': 'cm'})
    arm_circumference = IntegerField(u'Arm circumference', validators=[InputRequired(), NumberRange(20,40)], render_kw={'um': 'cm'})
    
    submit = SubmitField(u'Start test')

