import os
import secrets
import time
import calendar
from PIL import Image
from datetime import date, datetime, timedelta
from flask import render_template, url_for, flash, redirect, request, abort
from hospital import app, db, bcrypt, mail, socketio
from hospital.models import User, Doctor, Admin, Appointment, Timing, Eprescription, Medicine, Cart, Cartitem, Order, Ordereditem, Announcement
from hospital.forms import (AnnouncementForm, AppointmentForm, RegistrationForm, UserRegistrationForm, DoctorRegistrationForm, TimingForm,
                              MedicineForm, UpdateCartForm, AdminRegistrationForm ,EprescriptionForm, LoginForm, UpdateAccountForm, RequestResetForm,
                              CheckAppointmentForm, ResetPasswordForm, ChooseMedicineForm, UpdateMedicineForm, ChooseDoctorForm, specialist_choices, doctor_list)
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
from flask_socketio import SocketIO, join_room, leave_room, send


users_count = User.query.count()
doctors_count = Doctor.query.count()
admin_count = Admin.query.count()
count = users_count + doctors_count + admin_count
print(count)


# Predefined rooms for chat
ROOMS = ["lounge", "premium"]


@app.route("/")
@app.route("/home")
def home():
    try:
        user = User.query.filter_by(username=current_user.username).first()
        doc = Doctor.query.filter_by(username=current_user.username).first()
        admin = Admin.query.filter_by(username=current_user.username).first()
        if user:
            flag = 1
        elif doc:
            flag = 2
        elif admin:
            flag = 3
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


def send_registration_mail(user):
    msg = Message("Thank you for registering on Life Care",
                  sender='soumyajit660@gmail.com',
                  recipients=[user.email])
    msg.body = f'''Welcome {user.username} to Life Care. To view our website, visit the following link: 
{url_for('home', _external=True)}
We give flat 20% off on every order. You'll get 30% off on your first order from Life care. 
If you have not registered on our webpage then simply ignore this email and no changes will be made.
'''
    mail.send(msg)


@app.route("/user_register", methods=['GET', 'POST'])
def user_register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = UserRegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        global count
        count += 1
        user = User(id=count, username=form.username.data, email=form.email.data, password=hashed_password, 
                                    address=form.address.data, state=form.state.data, city=form.city.data, zipcode=form.zipcode.data, phone_number=form.phonenumber.data)
        print(f'IN USER - COUNT = {count}')
        db.session.add(user)
        db.session.commit()
        cart = Cart(user_id=count)
        db.session.add(cart)
        db.session.commit()
        user = User.query.filter_by(email=form.email.data).first()
        #send_registration_mail(user)
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
        user = Doctor(id=count, username=form.username.data, email=form.email.data, password=hashed_password, description=form.description.data, 
                                consultation_fee=form.consultation_fee.data, location=form.location.data, specialist=dict(specialist_choices).get(form.specialist.data))
        doc_timing = Timing(id=count)
        db.session.add(doc_timing)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('doctor_register.html', title='Doctor-Register', form=form)


@app.route('/admin_register', methods=['GET', 'POST'])
def admin_register():
    form = AdminRegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        global count
        count += 1
        admin = Admin(id=count, username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(admin)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('admin_register.html', title='Admin-Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            user = Doctor.query.filter_by(email=form.email.data).first()
            if user is None:
               user = Admin.query.filter_by(email=form.email.data).first() 
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
                  sender='soumyajit660@gmail.com',
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
            if user is None:
                user = Admin.query.filter_by(email=form.email.data).first()
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
        user = Admin.verify_reset_token(token)
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


@app.route("/chat", methods=['GET', 'POST'])
def chat():

    if not current_user.is_authenticated:
        flash('Please login', 'danger')
        return redirect(url_for('login'))

    return render_template("chat.html", username=current_user.username, rooms=ROOMS)



@app.route("/book_appointment", methods=['GET', 'POST'])
@login_required
def new_appointment():
    form = AppointmentForm()
    if form.validate_on_submit():
        today = date.today()
        if form.date.data <= today:
            flash("You cannot choose today's or any previous date!", 'danger')
            return redirect(url_for('new_appointment'))
        else:
            name = dict(doctor_list).get(form.doctor.data)
            doctor = Doctor.query.filter_by(username=name).first()
            times = Timing.query.filter_by(doctor=doctor).first()
            #LOGIC for date handling
            day = form.date.data 
            day_of_week = calendar.day_name[day.weekday()].lower()
            if day_of_week == 'monday' and not times.monday:
                flash(doctor.username+" doesn't attend patients on "+day_of_week, 'danger') 
                return redirect(url_for('new_appointment'))
            elif day_of_week == 'tuesday' and not times.tuesday:
                flash(doctor.username+" doesn't attend patients on "+day_of_week, 'danger') 
                return redirect(url_for('new_appointment'))
            elif day_of_week == 'wednesday' and not times.wednesday:
                flash(doctor.username+" doesn't attend patients on "+day_of_week, 'danger') 
                return redirect(url_for('new_appointment'))
            elif day_of_week == 'thursday' and not times.thursday:
                flash(doctor.username+" doesn't attend patients on "+day_of_week, 'danger') 
                return redirect(url_for('new_appointment'))
            elif day_of_week == 'friday' and not times.friday:
                flash(doctor.username+" doesn't attend patients on "+day_of_week, 'danger') 
                return redirect(url_for('new_appointment'))
            elif day_of_week == 'saturday' and not times.saturday:
                flash(doctor.username+" doesn't attend patients on "+day_of_week, 'danger') 
                return redirect(url_for('new_appointment'))
            elif day_of_week == 'sunday' and not times.sunday:
                flash(doctor.username+" doesn't attend patients on "+day_of_week, 'danger') 
                return redirect(url_for('new_appointment'))

            chosen_date = datetime.combine(form.date.data, datetime.min.time())
            appointment_on_chosen_date = Appointment.query.filter_by(doctor=doctor).filter_by(booked_for=chosen_date).first()
            if appointment_on_chosen_date:
                flash('You have already booked an appointment with this doctor on this date!', 'danger')
                return redirect(url_for('new_appointment'))
            print(appointment_on_chosen_date)
            print(f'Form date {form.date.data}')
            print(f'Doctor {doctor}')
            if day_of_week == 'monday':
                appointment = Appointment(booked_for=form.date.data, booked_for_time=times.monday,doctor_id=doctor.id, user=current_user)
            elif day_of_week == 'tuesday':
                appointment = Appointment(booked_for=form.date.data, booked_for_time=times.tuesday,doctor_id=doctor.id, user=current_user)
            elif day_of_week == 'wednesday':
                appointment = Appointment(booked_for=form.date.data, booked_for_time=times.wednesday,doctor_id=doctor.id, user=current_user)
            elif day_of_week == 'thursday':
                appointment = Appointment(booked_for=form.date.data, booked_for_time=times.thursday,doctor_id=doctor.id, user=current_user)
            elif day_of_week == 'friday':
                appointment = Appointment(booked_for=form.date.data, booked_for_time=times.friday,doctor_id=doctor.id, user=current_user)
            elif day_of_week == 'saturday':
                appointment = Appointment(booked_for=form.date.data, booked_for_time=times.saturday,doctor_id=doctor.id, user=current_user)
            elif day_of_week == 'sunday':
                appointment = Appointment(booked_for=form.date.data, booked_for_time=times.sunday,doctor_id=doctor.id, user=current_user)
            db.session.add(appointment)
            db.session.commit()
            e_prescription = Eprescription(id=appointment.id,user=current_user, doctor_id=doctor.id)
            db.session.add(e_prescription)
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
        today = date.today()
        day = form.date.data 
        day_of_week = calendar.day_name[day.weekday()].lower()
        date_after_three_months = today + timedelta(days=90)
        if form.date.data <= today:
            flash("Please choose a valid date! You cannot update the date to today's date or any previous date.", 'danger')
            return redirect(url_for('update_appointment', appointment_id=appointment.id))
        if form.date.data >= date_after_three_months:
            flash("You cannot book an appointment 3 months in advance!", 'danger')
            return redirect(url_for('update_appointment', appointment_id=appointment.id))
        name = dict(doctor_list).get(form.doctor.data)
        doctor = Doctor.query.filter_by(username=name).first()
        times = Timing.query.filter_by(doctor=doctor).first()
        
        if day_of_week == 'monday' and not times.monday:
            flash(doctor.username+" doesn't attend patients on "+day_of_week, 'danger') 
            return redirect(url_for('update_appointment',appointment_id=appointment_id))
        elif day_of_week == 'tuesday' and not times.tuesday:
            flash(doctor.username+" doesn't attend patients on "+day_of_week, 'danger') 
            return redirect(url_for('update_appointment',appointment_id=appointment_id))
        elif day_of_week == 'wednesday' and not times.wednesday:
            flash(doctor.username+" doesn't attend patients on "+day_of_week, 'danger') 
            return redirect(url_for('update_appointment',appointment_id=appointment_id))
        elif day_of_week == 'thursday' and not times.thursday:
            flash(doctor.username+" doesn't attend patients on "+day_of_week, 'danger') 
            return redirect(url_for('update_appointment',appointment_id=appointment_id))
        elif day_of_week == 'friday' and not times.friday:
            flash(doctor.username+" doesn't attend patients on "+day_of_week, 'danger') 
            return redirect(url_for('update_appointment',appointment_id=appointment_id))
        elif day_of_week == 'saturday' and not times.saturday:
            flash(doctor.username+" doesn't attend patients on "+day_of_week, 'danger') 
            return redirect(url_for('update_appointment',appointment_id=appointment_id))
        elif day_of_week == 'sunday' and not times.sunday:
            flash(doctor.username+" doesn't attend patients on "+day_of_week, 'danger') 
            return redirect(url_for('update_appointment',appointment_id=appointment_id))

        if day_of_week == 'monday':
            booked_for_time = times.monday
        elif day_of_week == 'tuesday':
            booked_for_time = times.tuesday
        elif day_of_week == 'wednesday':
            booked_for_time = times.wednesday
        elif day_of_week == 'thursday':
            booked_for_time = times.thursday
        elif day_of_week == 'friday':
            booked_for_time = times.friday
        elif day_of_week == 'saturday':
            booked_for_time = times.saturday
        elif day_of_week == 'sunday':
            booked_for_time = times.sunday

        appointment.doctor = doctor
        appointment.booked_for = form.date.data
        db.session.commit()
        flash('Your appointment has been updated!', 'success')
        return redirect(url_for('appointment_history', username=current_user.username))
    elif request.method == 'GET':
        form.doctor.data = appointment.doctor.username
        form.date.data = appointment.booked_for
    return render_template('new_appointment.html', title='Update appointment',
                           form=form, legend='Update Appointment', appointment=appointment)


@app.route("/appointment/<int:appointment_id>/delete", methods=['POST'])
@login_required
def delete_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    eprescription = Eprescription.query.get_or_404(appointment_id)
    if appointment.user != current_user:
        abort(403)
    db.session.delete(appointment)
    db.session.delete(eprescription)
    db.session.commit()
    flash('Your appointment has been deleted!', 'success')
    return redirect(url_for('appointment_history', title="Appointment-History", username=current_user.username))



@app.route("/appointment_history/<string:username>", methods=['GET', 'POST'])
def appointment_history(username):
    now = datetime.now()
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    appointments = Appointment.query.filter_by(user=user)\
        .order_by(Appointment.booked_on.desc())\
        .paginate(page=page, per_page=10)
    return render_template("booked_appointments.html", title="Appointment-History", appointments=appointments, user=user, now=now)


@app.route('/show_appointment_history/<string:date>', methods=['GET', 'POST'])
def show_history(date):
    has_appointment = True
    page = request.args.get('page', 1, type=int)
    doctor = Doctor.query.filter_by(username=current_user.username).first_or_404()
    format = "%m-%d-%Y"
    str_date = datetime.strptime(date, format)
    appointments = Appointment.query.filter_by(doctor=doctor).filter_by(booked_for=str_date)\
        .order_by(Appointment.booked_on.desc())\
        .paginate(page=page, per_page=10)
    check = Appointment.query.filter_by(doctor=doctor).filter_by(booked_for=str_date).first()
    if not check:
        has_appointment = False
    return render_template('show_booked_appointments.html', title="Appointment history by date", date=str_date, flag=has_appointment, appointments=appointments, doctor=doctor)


@app.route('/appointments_history', methods=['GET', 'POST'])
def appointment_history_by_date():
    doctor = Doctor.query.filter_by(username=current_user.username).first_or_404()
    form = CheckAppointmentForm()
    if form.validate_on_submit():
        date_to_check = form.date.data
        string_date_to_check = date_to_check.strftime("%m-%d-%Y")
        return redirect(url_for('show_history', date=string_date_to_check))
    return render_template('check_appointment_history_by_date.html', title="Appointment history by date",form=form)


@app.route("/appointments_history/<string:username>/all", methods=['GET', 'POST'])
def doc_appointment_history(username):
    has_appointment = True
    page = request.args.get('page', 1, type=int)
    doctor = Doctor.query.filter_by(username=username).first_or_404()
    appointments_with = Appointment.query.filter_by(doctor=doctor)\
        .order_by(Appointment.booked_on.desc())\
        .paginate(page=page, per_page=5)
    check = Appointment.query.filter_by(doctor=doctor).first()
    if not check:
        has_appointment = False
    return render_template('doc_booked_appointments.html', title="Appointment-history",flag=has_appointment, appointments_with=appointments_with, doctor=doctor)


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


@app.route('/doc_e_prescription/<int:prescription_id>', methods=['GET', 'POST'])
def doc_e_prescription(prescription_id):
    prescription = Eprescription.query.get(prescription_id)
    form = EprescriptionForm()
    if form.validate_on_submit():
        prescription.content = form.content.data
        db.session.commit()
        flash('Your prescription has been saved!', 'success')
        return redirect(url_for('doc_appointment_history', username=current_user.username))
    elif request.method == 'GET':
        form.content.data = prescription.content
    return render_template('doc_e_prescription.html', title="Edit-Prescription", form=form)


@app.route('/user_e_prescription/<int:prescription_id>', methods=['GET', 'POST'])
def user_e_prescription(prescription_id):
    has_prescribed = True
    prescription = Eprescription.query.get(prescription_id)
    if not prescription:
        has_prescribed = False
    return render_template('user_e_prescription.html', title="View-Prescription", prescription=prescription, flag=has_prescribed)


# def save_med_picture(form_picture):
#     random_hex = secrets.token_hex(8)
#     _, f_ext = os.path.splitext(form_picture.filename)
#     picture_fn = random_hex + f_ext
#     picture_path = os.path.join(app.root_path, 'static/images/meds/', picture_fn)

#     output_size = (200, 200)
#     i = Image.open(form_picture)
#     i.thumbnail(output_size)
#     i.save(picture_path)

#     return picture_fn

@app.route('/add_medicine', methods=['GET', 'POST'])
def add_medicine():
    form = MedicineForm()
    if form.validate_on_submit():
        medicine = Medicine(name=form.name.data, disease=form.disease.data, image_file=form.picture.data, manufactured_by=form.manufactured_by.data,
                                price=form.price.data, stock=form.stock.data, description=form.description.data, uses=form.uses.data, side_effects=form.side_effects.data, substitutes=form.substitutes.data)
        db.session.add(medicine)
        db.session.commit()
        flash('Your medicine info has been saved!', 'success')
        return redirect(url_for('add_medicine'))
    return render_template('add_medicine.html', title="Add Medicine", form=form)


@app.route('/medicines', methods=['GET', 'POST'])
@login_required
def medicines_disease():
    return render_template('medicines.html', title="View Medicines", medicines=None)


@app.route('/medicines/<string:disease_type>', methods=['GET', 'POST'])
def medicines(disease_type):
    page = request.args.get('page', 1, type=int)
    medicines = Medicine.query.filter_by(disease=disease_type).paginate(page=page, per_page=5)
    return render_template('medicines.html', medicines=medicines, title="View medicines for"+disease_type, disease_type=disease_type)


@app.route('/medicine_display/<int:medicine_id>', methods=['GET', 'POST'])
def medicine_display(medicine_id):
    med = Medicine.query.get(medicine_id)
    substitute = med.substitutes
    if substitute:
        sub = Medicine.query.filter_by(name=substitute).first()
    else:
        sub=None
    return render_template('medicine_display.html', title="Description of medicine", med=med, sub=sub)


@app.route('/view_cart', methods=['GET', 'POST'])
def view_cart():
    grand_total = 0
    first_order = False
    page = request.args.get('page', 1, type=int)
    cartitems = Cartitem.query.filter_by(cart_id=current_user.id).paginate(page=page, per_page=5)
    for item in cartitems.items:
        grand_total += item.total_price 
    if Cartitem.query.filter_by(cart_id=current_user.id).first() is None:
        cartitems = None  
    first_order = Order.query.filter_by(user=current_user).first()
    if not first_order:
        first_order = True
    return render_template('view_cart.html', title="Shopping Cart", cartitems=cartitems, grand_total=grand_total, flag=first_order)


@app.route('/add_to_cart/<int:medicine_id>', methods=['GET', 'POST'])
@login_required
def add_to_cart(medicine_id):
    first_order = True
    order = Order.query.filter_by(user=current_user).first()
    if order:
        first_order = False
    try:
        grand_total = 0
        page = request.args.get('page', 1, type=int)
        med = Medicine.query.get(medicine_id)
        price=med.price
        cartitem = Cartitem(cart_id=current_user.id, medicine_id=medicine_id, quantity=1, total_price=price)
        db.session.add(cartitem)
        db.session.commit()
    except:
        flash('Some unexpected error occured!', 'danger')
        return redirect(url_for('view_cart', flag=first_order))
    page = request.args.get('page', 1, type=int)
    cartitems = Cartitem.query.filter_by(cart_id=current_user.id).paginate(page=page, per_page=5)
    for item in cartitems.items:
        grand_total += item.total_price 
    flash('Item added to cart', 'success')
    return render_template('view_cart.html', title="Shopping cart", cartitems=cartitems, grand_total=grand_total)


@app.route('/cart/<int:item_id>', methods=['GET', 'POST'])
def cart(item_id):
    item = Cartitem.query.get_or_404(item_id)
    print(f'ITEM {item}')
    return render_template('cartitem.html', title='Cart-Item', item=item)
    

# @app.route('/cart/<int:item_id>/update', methods=['GET', 'POST'])
# def update_cart(item_id):
#     citem = Cartitem.query.get(item_id)
#     form = UpdateCartForm()
#     if form.validate_on_submit():
#         if form.quantity.data <= 0:
#             flash('Please select a valid quantity', 'danger')
#             return redirect(url_for('update_cart', item_id=citem.id))
#         elif form.quantity.data > 4:
#             flash('Upto 4 stocks can be given per user', 'warning')
#             return redirect(url_for('update_cart', item_id=citem.id))
#         citem.quantity = form.quantity.data
#         db.session.commit()
#         flash('Your cart has been updated', 'success')
#         return redirect(url_for('view_cart'))
#     elif request.method == 'GET':
#         form.quantity.data = citem.quantity
#     return render_template('cartitem.html', title="Update or Delete Cart", form=form, item=citem)



@app.route("/cart/<int:item_id>/update", methods=['GET', 'POST'])
@login_required
def update_cart(item_id):
    first_order = True
    item = Cartitem.query.get_or_404(item_id)
    med = Medicine.query.get(item.medicine_id)
    order = Order.query.filter_by(user=current_user).first()
    if order:
        first_order = False
    form = UpdateCartForm()
    if form.validate_on_submit():
        if form.quantity.data <= 0:
            flash('Please choose a valid quantity', 'danger')
            return redirect(url_for('update_cart', item_id=item_id))
        elif form.quantity.data > 4:
            flash('Only 4 quantity is allowed per person', 'warning')
            return redirect(url_for('update_cart', item_id=item_id))
        elif form.quantity.data > med.stock:
            flash("Sorry but we don't have that many stocks left", 'warning')
            return redirect(url_for('update_cart', item_id=item_id))
        item.quantity = form.quantity.data
        item.total_price = form.quantity.data * med.price
        db.session.commit()
        flash('Your shopping cart has been updated!', 'success')
        return redirect(url_for('view_cart', flag=first_order))
    elif request.method == 'GET':
        form.quantity.data = item.quantity
    return render_template('update_cart.html', title="Update or Delete Cart", form=form, item=item)


@app.route("/cart/<int:item_id>/delete", methods=['POST'])
@login_required
def delete_cart(item_id):
    first_order = True
    item = Cartitem.query.get_or_404(item_id)
    order = Order.query.filter_by(user=current_user).first()
    if order:
        first_order = False
    db.session.delete(item)
    db.session.commit()
    flash('Your item has been deleted!', 'success')
    print(f'FIRST ORDER {first_order}')
    return redirect(url_for('view_cart', flag=first_order))


def send_order_acknowledgement(user):
    msg = Message('Order placed successfully on Life Care',
                  sender='soumyajit660@gmail.com',
                  recipients=[user.email])
    msg.body = f'''Your order has been placed successfully!
To view your order history, visit the following link:
{url_for('order_history', _external=True)}
Hope you had an amazing time at our website, Thank you.


If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)


@app.route('/place_order', methods=['GET', 'POST'])
def place_order():
    total_amount = 0
    first_order = True
    orde = Order.query.filter_by(user=current_user).first()
    if orde:
        first_order = False
    my_cartitems = Cartitem.query.filter_by(cart_id=current_user.id).all()
    print(my_cartitems)
    if len(my_cartitems) == 0:
        flash("You don't have anything in your cart at the moment! Cannot place order.", 'warning')
        return redirect(url_for('view_cart', flag=first_order))
    for item in my_cartitems:
        total_amount += item.total_price
    order = Order.query.filter_by(user=current_user).first()
    if order is None:
        total_amount *= 0.7
    else:
        first_order = False
        total_amount *= 0.8
    print(first_order)
    if int(total_amount) < 500:
        flash('Total bill amount should be over 500 rupees!', 'warning')
        return redirect(url_for('view_cart', flag=first_order))
    if first_order:
        order = Order(bill_amount=total_amount*0.7, user_id=current_user.id)
    else:
        order = Order(bill_amount=total_amount*0.8, user_id=current_user.id)
    db.session.add(order)
    db.session.commit()
    current_order = Order.query.filter_by(user=current_user).order_by(Order.ordered_on.desc()).first()
    if first_order:
        for item in my_cartitems:
            my_ordered_items = Ordereditem(order_id=current_order.id, medicine_name=item.medicine.name, medicine_image=item.medicine.image_file, quantity=item.quantity, total_price=item.total_price*0.7)
            item.medicine.stock -= item.quantity
            db.session.add(my_ordered_items)
            db.session.delete(item)
    else:
        for item in my_cartitems:
            my_ordered_items = Ordereditem(order_id=current_order.id, medicine_name=item.medicine.name, medicine_image=item.medicine.image_file, quantity=item.quantity, total_price=item.total_price*0.8)
            item.medicine.stock -= item.quantity
            db.session.add(my_ordered_items)
            db.session.delete(item)
    db.session.commit()
    # send_order_acknowledgement(current_user)
    flash('Your order has been placed!', 'success')
    return render_template('order_acknowledgement.html', title="Order Placed Successfully")

@app.route('/order_history', methods=['GET', 'POST'])
def order_history():
    page = request.args.get('page', 1, type=int)
    orders = Order.query.filter_by(user_id=current_user.id).paginate(page=page, per_page=10)
    return render_template('order_history.html', title="Order History", orders=orders)


@app.route('/order_history/<int:order_id>', methods=['GET', 'POST'])
def order_details(order_id):
    total = 0
    page = request.args.get('page', 1, type=int)
    items = Ordereditem.query.filter_by(order_id=order_id).paginate(page=page, per_page=10)
    for item in items.items:
        total += item.total_price
    return render_template('order_details.html', title="Order Details", items=items, order_id=order_id, total=total)

@app.route('/necessary_information', methods=['GET', 'POST'])
def necessary_information():
    return render_template('important_contacts.html', title="Necessary information")

@app.route('/necessary_hospital_info', methods=['GET', 'POST'])
def important_hospital_contacts():
    return render_template('important_hospital_contacts.html', title="Hospital Contacts")

@app.route('/necessary_bloodbank_info', methods=['GET', 'POST'])
def important_blood_bank_contacts():
    return render_template('important_blood_bank_contacts.html', title="Blood Bank Contacts")


@app.route('/nearby_map')
def nearby_map():
    return render_template('nearby_maps.html')


@app.route("/nearby_hospitals")
@login_required
def nearby_hospital_map():
    return render_template('hospital_map.html')


@app.route("/nearby_bloodbnaks")
@login_required
def nearby_bloodbank_map():
    return render_template('bloodbank_map.html')


@app.route("/nearby_medical_stores")
@login_required
def nearby_medical_stores_map():
    return render_template('medical_store_map.html')

@app.route('/make_announcement', methods=['GET', 'POST'])
@login_required
def make_announcement():
    users_list = []
    form = AnnouncementForm()
    if form.validate_on_submit():
        announcement = Announcement(title=form.title.data, content=form.content.data ,admin=current_user)
        users = User.query.all()
        for user in users:
            users_list.append(user.email)
        msg = Message(form.title.data,
                  sender='soumyajit660@gmail.com',
                  recipients=users_list)
        header = "This mail is from Life Care.\n\n"
        footer = "If you are not a user of Life Care, then simply ignore this email and no changes will be made. Sorry for the inconvinience"
        msg.body = f'{header}\n{form.content.data}\n\n{footer}'
        mail.send(msg)
        db.session.add(announcement)
        db.session.commit()
        flash('Your mail has been sent!', 'success')
        # Redirect to announcement history
        return redirect(url_for('view_announcement'))
    return render_template("new_announcement.html", title="New announcement", form=form)


@app.route('/view_announcements', methods=['GET'])
def view_announcement():
    page = request.args.get('page', 1, type=int)
    announcements = Announcement.query.order_by(Announcement.created_on.desc())\
        .paginate(page=page, per_page=5)
    return render_template("view_announcements.html", title="View announcements", announcements=announcements)


@app.route('/update_medicine', methods=['GET', 'POST'])
def choose_medicine():
    form = ChooseMedicineForm()
    if form.validate_on_submit():
        medicine = form.medicine.data
        return redirect(url_for('update_medicine', medicine_name=medicine))
    return render_template('choose_medicine.html', title="Update Medicine", form=form)


@app.route('/update_medicine/<string:medicine_name>', methods=['GET', 'POST'])
def update_medicine(medicine_name):
    medicine = Medicine.query.filter_by(name=medicine_name).first()
    form = UpdateMedicineForm()
    if request.method == 'GET':
        form.disease.data = medicine.disease
        form.picture.data = medicine.image_file
        form.manufactured_by.data = medicine.manufactured_by
        form.price.data = medicine.price
        form.stock.data = medicine.stock
        form.description.data = medicine.description
        form.uses.data = medicine.uses
        form.side.data = medicine.side_effects
        form.substitutes.data = medicine.substitutes
    elif form.validate_on_submit():
        medicine.disease = form.disease.data
        medicine.image_file = form.picture.data
        medicine.manufactured_by = form.manufactured_by.data
        medicine.price = form.price.data
        medicine.stock = form.stock.data
        medicine.description = form.description.data
        medicine.uses = form.uses.data
        medicine.side_effects = form.side.data
        medicine.substitutes = form.substitutes.data
        db.session.commit()
        flash('Your medicine info has been updated', 'success')
        return redirect(url_for('choose_medicine'))
    return render_template('update_medicine.html', title="Update medicine", form=form)


@app.route('/all_doctors', methods=['GET', 'POST'])
def all_doctors():
    page = request.args.get('page', 1, type=int)
    doctors = Doctor.query.paginate(page=page, per_page=15)
    return render_template('all_doctors.html', title="All doctors", doctors=doctors)


@app.route('/choose_doctor', methods=['GET', 'POST'])
def choose_doctor():
    form = ChooseDoctorForm()
    if form.validate_on_submit():
        speciality = form.speciality.data
        return redirect(url_for('specialist_doctor', speciality=speciality))
    return render_template('choose_doctor.html', title="Choose a doctor", form=form)
        
@app.route('/choose_doctor/<string:speciality>', methods=['GET', 'POST'])
def specialist_doctor(speciality):
    page = request.args.get('page', 1, type=int)
    doctors = Doctor.query.filter_by(specialist=speciality).paginate(page=page, per_page=15)
    return render_template('specialist_doctor.html', title="Specialist doctor", doctors=doctors, speciality=speciality)


@app.route('/doctor_description/<int:doctor_id>', methods=['GET', 'POST'])
def doctor_description(doctor_id):
    doc = Doctor.query.get_or_404(doctor_id)
    timing = Timing.query.get_or_404(doctor_id)
    return render_template('doctor_description.html', title="Doctor description", doc=doc, timing=timing)

        
@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404


@socketio.on('incoming-msg')
def on_message(data):
    """Broadcast messages"""

    msg = data["msg"]
    username = data["username"]
    room = data["room"]
    # Set timestamp
    time_stamp = datetime.utcnow().strftime('%b-%d %I:%M%p')
    send({"username": username, "msg": msg, "time_stamp": time_stamp}, room=room)


@socketio.on('join')
def on_join(data):
    """User joins a room"""

    username = data["username"]
    room = data["room"]
    join_room(room)

    # Broadcast that new user has joined
    send({"msg": username + " has joined the " + room + " room."}, room=room)


@socketio.on('leave')
def on_leave(data):
    """User leaves a room"""

    username = data['username']
    room = data['room']
    leave_room(room)
    send({"msg": username + " has left the room"}, room=room)