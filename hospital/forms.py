
import re
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import IntegerField, StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, FloatField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from hospital import app
from hospital.models import User, Appointment, Doctor, Eprescription, Medicine, Admin


specialist_choices = [('Family Physician', 'Family Physician'), ('Internal Medicine Physician', 'Internal Medicine Physician'), ('Pediatrician', 'Pediatrician'), ('Obstetrician/Gynecologist', 'Obstetrician/Gynecologist'),
                         ('Surgeon', 'Surgeon'), ('Psychiatrist', 'Psychiatrist'), ('Cardiologist', 'Cardiologist'), ('Dermatologist', 'Dermatologist'), ('Endocrinologist', 'Endocrinologist'), ('Gastroenterologist', 'Gastroenterologist'), 
                         ('Gastroenterologist', 'Gastroenterologist'), ('Infectious Disease Physician', 'Infectious Disease Physician'), ('Nephrologist', 'Nephrologist'), ('Ophthalmologist', 'Ophthalmologist'), ('Otolaryngologist', 'Otolaryngologist'),
                         ('Pulmonologist', 'Pulmonologist'), ('Neurologist', 'Neurologist'), ('Physician Executive', 'Physician Executive'), ('Radiologist', 'Radiologist'), ('Anesthesiologist', 'Anesthesiologist'), ('Oncologist', 'Oncologist')]
specialist_choices.sort()

state_list = [('Andhra Pradesh', 'Andhra Pradesh'), ('Arunachal Pradesh', 'Arunachal Pradesh'), ('Assam', 'Assam'), ('Bihar', 'Bihar'), ('Chhattisgarh', 'Chhattisgarh'), ('Goa', 'Goa'),
                    ('Gujarat', 'Gujarat'), ('Haryana', 'Haryana'), ('Himachal Pradesh', 'Himachal Pradesh'), ('Jharkhand', 'Jharkhand'), ('Karnataka', 'Karnataka'), ('Kerala', 'Kerala'),
                    ('Madhya Pradesh', 'Madhya Pradesh'), ('Maharashtra', 'Maharashtra'), ('Manipur', 'Manipur'), ('Meghalaya', 'Meghalaya'), ('Mizoram', 'Mizoram'), ('Nagaland', 'Nagaland'), 
                    ('Odisha', 'Odisha'), ('Punjab', 'Punjab'), ('Rajasthan', 'Rajasthan'), ('Sikkim', 'Sikkim'), ('Tamil Nadu', 'Tamil Nadu'), ('Telangana', 'Telangana'), ('Tripura', 'Tripura'),
                    ('Uttar Pradesh', 'Uttar Pradesh'), ('Uttarakhand', 'Uttarakhand'), ('West Bengal', 'West Bengal')]

doctor_list = []
medicine_list = []

docs = Doctor.query.all()
for doc in docs:
    doctor_list.append((doc.username, doc.username))
doctor_list.sort()

medicines = Medicine.query.all()
for medicine in medicines:
    medicine_list.append((medicine.name, medicine.name))
medicine_list.sort()

class RegistrationForm(FlaskForm):
    yes_doctor = BooleanField('Yes')
    no_doctor = BooleanField('No')
    submit = SubmitField('Go')


class UserRegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    address = StringField('Address', validators=[DataRequired()])
    state = SelectField(u'State', choices=state_list)
    city = StringField('City', validators=[DataRequired()])
    zipcode = StringField('Zipcode', validators=[DataRequired()])
    phonenumber = StringField('Phone Number', validators=[DataRequired()])
    submit = SubmitField('Sign Up')


    def validate_phonenumber(self, phonenumber):
        ph_no = phonenumber.data
        fresh = ph_no.strip()
        if len(fresh) != 10:
            raise ValidationError('This is not a valid Phone number! Please enter a valid one')

    def validate_zipcode(self, zipcode):
        code = re.compile(r"\s*(\w\d\s*){3}\s*")
        if not code.match(zipcode.data):
            raise ValidationError('This is not a valid Zipcode! Please enter a valid one')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')


class AdminRegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = Admin.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = Admin.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')


class DoctorRegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    description = TextAreaField('Tell us about your achievements', validators=[DataRequired()])
    specialist = SelectField(u'Specialist', choices=specialist_choices)
    consultation_fee = IntegerField('Consultation fee', validators=[DataRequired()])
    location = StringField('Chamber Address', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = Doctor.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = Doctor.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class UpdateAccountForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is taken. Please choose a different one.')
            alt_user = Doctor.query.filter_by(username=username.data).first()
            if alt_user:
                raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is taken. Please choose a different one.')
            alt_user = Doctor.query.filter_by(email=email.data).first()
            if alt_user:
                raise ValidationError('That username is taken. Please choose a different one.')


class RequestResetForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            user = Doctor.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account with that email. You must register first.')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')


class AppointmentForm(FlaskForm):
    doctor = SelectField(u'Doctor', choices=doctor_list)
    date = DateField('Date',format='%Y-%m-%d')
    submit = SubmitField('Book Appointment')


class CheckAppointmentForm(FlaskForm):
    date = DateField('Choose a Date',format='%Y-%m-%d')
    submit = SubmitField('Check')

class TimingForm(FlaskForm):
    monday = StringField('Monday')
    tuesday = StringField('Tuesday')
    wednesday = StringField('Wednesday')
    thursday = StringField('Thursday')
    friday = StringField('Friday')
    saturday = StringField('Saturday')
    sunday = StringField('Sunday')
    submit = SubmitField('Save Timings')


class EprescriptionForm(FlaskForm):
    content = TextAreaField('Prescribe')
    submit = SubmitField('Save Prescription')

class MedicineForm(FlaskForm):
    name = StringField('Medicine name', validators=[DataRequired()])
    disease = StringField('Disease', validators=[DataRequired()])
    # picture = FileField('Upload medicine picture', validators=[FileAllowed(['jpg', 'jpeg', 'png'])])
    picture = StringField('Picture filename')
    manufactured_by = StringField('Manufactured by', validators=[DataRequired()])
    price = FloatField('Price')
    stock = IntegerField('Stock', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    uses = TextAreaField('Uses', validators=[DataRequired()])
    side_effects = TextAreaField('Side Effects')
    substitutes = StringField('Substitute')
    submit = SubmitField('Add Medicine')

class UpdateCartForm(FlaskForm):
    quantity = IntegerField('Select quantity', validators=[DataRequired()])
    submit = SubmitField('Submit')

class AnnouncementForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Submit')

class ChooseMedicineForm(FlaskForm):
    medicine = SelectField(u'Medicine name', choices=medicine_list)
    submit = SubmitField('Submit')

class UpdateMedicineForm(FlaskForm):
    disease = StringField('Disease', validators=[DataRequired()])
    # picture = FileField('Upload medicine picture', validators=[FileAllowed(['jpg', 'jpeg', 'png'])])
    picture = StringField('Picture filename')
    manufactured_by = StringField('Manufactured by', validators=[DataRequired()])
    price = FloatField('Price')
    stock = IntegerField('Stock', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    uses = TextAreaField('Uses', validators=[DataRequired()])
    side = TextAreaField('Side Effects', validators=[DataRequired()])
    substitutes = StringField('Substitute')
    submit = SubmitField('Update Medicine')

class ChooseDoctorForm(FlaskForm):
    speciality = SelectField(u'Type of Doctor', choices=specialist_choices)
    submit = SubmitField('Submit')

