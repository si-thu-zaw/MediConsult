from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, RadioField, SelectField
from wtforms.fields.html5 import DateField
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, Length, EqualTo, Email, ValidationError
from mediconsult.models import User, userrole_query

class RegistrationForm(FlaskForm):
    username = StringField('Username', 
                           validators=[DataRequired(), Length(min=5, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', 
                             validators=[DataRequired()])
    password_confirm = PasswordField('Confirm Password', 
                                     validators=[DataRequired(), EqualTo('password')])
    role = SelectField('User Role', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Complete Registraiton')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('The chosen username is taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('This email already exists. Please use a different email for a new account')
        
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', 
                             validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')    
    
class UpdateAccountForm(FlaskForm):
    username = StringField('Username', 
                           validators=[DataRequired(), Length(min=5, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    
    submit = SubmitField('Update')
    
    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('The chosen username is taken. Please choose a different one.')
    
    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('This email already exists. Please use a different email for a new account')

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    postcontent = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Post')
    
class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')
    
    def validate_username(self, username):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('The email entered does not exist. Please create a new account.')
        
class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', 
                             validators=[DataRequired()])
    password_confirm = PasswordField('Confirm Password', 
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class ChangePasswordForm(FlaskForm):
    password = PasswordField('Current Password', 
                             validators=[DataRequired()])
    new_password = PasswordField('New Password', 
                             validators=[DataRequired()])
    new_password_confirm = PasswordField('Confirm New Password', 
                                     validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')

class AdminChangePasswordForm(FlaskForm):
    new_password = PasswordField('New Password', 
                             validators=[DataRequired()])
    new_password_confirm = PasswordField('Confirm New Password', 
                                     validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')

class MOTDForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    motdcontent = TextAreaField('Message Content', validators=[DataRequired()])
    submit = SubmitField('Post')

class NewPatientForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    dob = DateField('Date of Birth', format='%Y-%m-%d')
    gender = RadioField('Gender', choices=[('Male','Male'), ('Female','Female')], validators=[DataRequired()])
    address = StringField("Patient's Address", validators=[DataRequired()])
    contact_no = StringField("Patient's Phone Number", validators=[DataRequired()])
    submit = SubmitField('Post')

class NewCaseForm(FlaskForm):
    patient = SelectField('Select Your Patient', coerce=int, validators=[DataRequired()])
    title = StringField("Case Title", validators=[DataRequired()])
    casecontent = TextAreaField("Describe the case here", validators=[DataRequired()])
    submit = SubmitField('Post')

class NoteForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    notecontent = TextAreaField('Note Content', validators=[DataRequired()])
    submit = SubmitField('Post')   

        
class ReferralForm(FlaskForm):
    comment = StringField('Referral Details', validators=[DataRequired()])
    date = DateField('Date of Referral', format='%Y-%m-%d')
    submit = SubmitField('Post')

class HistoryForm(FlaskForm):
    general = TextAreaField("General Background")
    medical = TextAreaField("Medical Background")
    family = TextAreaField("Family Medical History")
    personal = TextAreaField("Personal History")
    submit = SubmitField('Post')

class CommentForm(FlaskForm):
    commentcontent = TextAreaField('Comment', validators=[DataRequired()])
    submit = SubmitField('Post')

class ResultForm(FlaskForm):
    comment = TextAreaField("Result Description and Details", validators=[DataRequired()])
    file = FileField('Upload File')
    submit = SubmitField('Upload')

class PrescriptionForm(FlaskForm):
    medication = StringField('Medication', validators=[DataRequired()])
    frequency = RadioField('Frequency', choices=[('OM', 'OM'), ('ON', 'ON'),('TDS', 'TDS'), ('BDS', 'BDS'), ('IND', 'IND'), ('PRN', 'PRN')], validators=[DataRequired()])    
    period = StringField('Prescription Period', validators=[DataRequired()])
    comment = StringField('Prescription Details', validators=[DataRequired()])
    submit = SubmitField('Submit')