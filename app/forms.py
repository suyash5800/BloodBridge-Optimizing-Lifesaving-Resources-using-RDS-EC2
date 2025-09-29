from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, DateTimeLocalField
from wtforms.validators import DataRequired, Optional

class ApproveRejectForm(FlaskForm):
    admin_notes = TextAreaField('Admin Notes (Optional)', validators=[Optional()])
    submit = SubmitField('Submit')

class BloodDriveForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    location = StringField('Location', validators=[DataRequired()])
    start_date = DateTimeLocalField('Start Date & Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    end_date = DateTimeLocalField('End Date & Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    submit = SubmitField('Submit Blood Drive') 