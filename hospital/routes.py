import os
import secrets
from PIL import Image
from datetime import date
from flask import render_template, url_for, flash, redirect, request, abort
from hospital import app, db, bcrypt, mail
from hospital.models import User, Doctor, Appointment, Timing, Eprescription
from hospital.forms import (AppointmentForm, RegistrationForm, UserRegistrationForm, DoctorRegistrationForm, TimingForm, 
                              LoginForm, UpdateAccountForm, RequestResetForm, ResetPasswordForm, specialist_choices, doctor_list)
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message

count = 0

@app.route("/")
@app.route("/home")
def home():
    try:
        user = User.query.filter_by(username=current_user.username).first()
        doc = Doctor.query.filter_by(username=current_user.username).first()
        if user:
            flag = 1
        elif doc:
            flag = 2
    except:
        flag = 0
    return render_template('home.html',flag=flag)


@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        if form.yes_doctor.data and form.no_doctor.data:
            flash('Please choose any one of the following!', 'danger')
        elif form.yes_doctor.data:
            return redirect(url_for('doctor_register'))
        elif form.no_doctor.data:
            return redirect(url_for('user_register'))
        elif not form.yes_doctor.data and not form.no_doctor.data:
            flash('You have to choose a option!', 'danger')     
    return render_template('register.html', form=form)


@app.route("/user_register", methods=['GET', 'POST'])
def user_register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = UserRegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        global count
        count += 1
        user = User(id=count, username=form.username.data, email=form.email.data, password=hashed_password)
        print(f'IN USER - COUNT = {count}')
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('user_register.html', title='User-Register', form=form)


@app.route("/doctor_register", methods=['GET', 'POST'])
def doctor_register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = DoctorRegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        global count
        count += 1
        print(f'IN DOCTOR - COUNT = {count}')
        user = Doctor(id=count, username=form.username.data, email=form.email.data, password=hashed_password, 
                                consultation_fee=form.consultation_fee.data, location=form.location.data, specialist=dict(specialist_choices).get(form.specialist.data))
        doc_timing = Timing(id=count)
        db.session.add(doc_timing)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('doctor_register.html', title='Doctor-Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            user = Doctor.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}
If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            user = Doctor.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = Normal.verify_reset_token(token)
    if user is None:
        user = Doctor.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)

@app.route("/nearby_medical_stores")
@login_required
def nearby_map():
    return render_template('new_map.html')


@app.route("/book_appointment", methods=['GET', 'POST'])
@login_required
def new_appointment():
    form = AppointmentForm()
    if form.validate_on_submit():
        today = date.today()
        if form.date.data < today:
            flash('Please choose a valid date!', 'danger')
            return redirect(url_for('new_appointment'))
        else:
            name = dict(doctor_list).get(form.doctor.data)
            doctor = Doctor.query.filter_by(username=name).first()
            appointment = Appointment(booked_for=form.date.data,doctor_id=doctor.id, user=current_user)
            db.session.add(appointment)
            db.session.commit()
            flash('Your appointment has been booked', 'success')
            return redirect(url_for('new_appointment'))
    return render_template('new_appointment.html', title='New Appointment', form=form)


@app.route("/appointment/<int:appointment_id>")
def appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    return render_template('appointment.html', title='Appointment with '+appointment.doctor.username, appointment=appointment)


@app.route("/appointment/<int:appointment_id>/update", methods=['GET', 'POST'])
@login_required
def update_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.user != current_user:
        abort(403)
    form = AppointmentForm()
    if form.validate_on_submit():
        name = dict(doctor_list).get(form.doctor.data)
        doctor = Doctor.query.filter_by(username=name).first()
        appointment.doctor = doctor
        db.session.commit()
        flash('Your appointment has been updated!', 'success')
        return redirect(url_for('appointment_history', username=current_user.username))
    elif request.method == 'GET':
        form.doctor.data = appointment.doctor.username
    return render_template('new_appointment.html', title='Update appointment',
                           form=form, legend='Update Appointment')


@app.route("/appointment/<int:appointment_id>/delete", methods=['POST'])
@login_required
def delete_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.user != current_user:
        abort(403)
    db.session.delete(appointment)
    db.session.commit()
    flash('Your appointment has been deleted!', 'success')
    return redirect(url_for('appointment_history', title="Appointment-History", username=current_user.username))



@app.route("/appointment_history/<string:username>", methods=['GET', 'POST'])
def appointment_history(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    print(f'User is {user}')
    appointments = Appointment.query.filter_by(user=user)\
        .order_by(Appointment.booked_on.desc())\
        .paginate(page=page, per_page=10)
    return render_template("booked_appointments.html", title="Appointment-History", appointments=appointments, user=user)


@app.route("/appointments_history/<string:username>", methods=['GET', 'POST'])
def doc_appointment_history(username):
    page = request.args.get('page', 1, type=int)
    doctor = Doctor.query.filter_by(username=username).first_or_404()
    appointments_with = Appointment.query.filter_by(doctor=doctor)\
        .order_by(Appointment.booked_on.desc())\
        .paginate(page=page, per_page=5)
    return render_template('doc_booked_appointments.html', title="Appointment-history", appointments_with=appointments_with, doctor=doctor)

@app.route("/timing/<string:doctor_name>", methods=['GET', 'POST'])
def timing(doctor_name):
    form = TimingForm()
    if form.validate_on_submit():
        timing = Timing.query.get(current_user.id)
        timing.monday = form.monday.data
        timing.tuesday = form.tuesday.data
        timing.wednesday = form.wednesday.data
        timing.thursday = form.thursday.data
        timing.friday = form.friday.data
        timing.saturday = form.saturday.data
        timing.sunday = form.sunday.data
        db.session.commit()
        flash('Your timings has been updated successfully', 'success')
        return redirect(url_for('timing', doctor_name=current_user.username))
    elif request.method == 'GET':
        timing = Timing.query.get(current_user.id)
        form.monday.data = timing.monday
        form.tuesday.data = timing.tuesday
        form.wednesday.data = timing.wednesday
        form.thursday.data = timing.thursday
        form.friday.data = timing.friday
        form.saturday.data = timing.saturday
        form.sunday.data = timing.sunday
    return render_template('timing.html', title='Update your timings', doctor_name=current_user.username, form=form)



