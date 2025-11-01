from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    class Meta:
        csrf = True
        csrf_time_limit = None
    
    username = StringField('اسم المستخدم', validators=[DataRequired()])
    password = PasswordField('كلمة المرور', validators=[DataRequired()])
    user_type = SelectField('نوع المستخدم', choices=[('admin', 'مدير'), ('employee', 'موظف')], validators=[DataRequired()])
    submit = SubmitField('دخول')
