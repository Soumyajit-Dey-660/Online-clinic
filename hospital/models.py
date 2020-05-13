from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from hospital import db, login_manager, app
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    if user is None:
        user = Doctor.query.get(int(user_id))
    return user


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    appointments = db.relationship('Appointment', backref='user', lazy=True)
    eprescriptions = db.relationship('Eprescription', backref='user', lazy=True)

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return NormalUser.query.get(user_id)

    def __repr__(self):
        return f"Normal-User('{self.username}', '{self.email}', '{self.image_file}')"


class Doctor(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    consultation_fee = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    specialist = db.Column(db.String(50), nullable=False)
    appointments = db.relationship('Appointment', backref='doctor', lazy=True)
    timings = db.relationship('Timing', backref='doctor', lazy=True)
    eprescriptions = db.relationship('Eprescription', backref='doctor', lazy=True)
    # posts = db.relationship('Post', backref='author', lazy=True)

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return DoctorUser.query.get(user_id)

    def __repr__(self):
        return f"Doctor('{self.username}', '{self.email}', '{self.image_file}')"


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    booked_on = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    booked_for = db.Column(db.DateTime, nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Timing(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('doctor.id'), primary_key=True)
    monday = db.Column(db.String(50), default=None)
    tuesday = db.Column(db.String(50), default=None)
    wednesday = db.Column(db.String(50), default=None)
    thursday = db.Column(db.String(50), default=None)
    friday = db.Column(db.String(50), default=None)
    saturday = db.Column(db.String(50), default=None)
    sunday = db.Column(db.String(50), default=None)

class Eprescription(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('appointment.id'), primary_key=True)
    content = db.Column(db.Text(), default=None)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(40), nullable=False)
    disease = db.Column(db.String(20), nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    manufactured_by = db.Column(db.String(40), nullable=False)
    price = db.Column(db.Float, default=None)
    description = db.Column(db.Text, nullable=False)
    uses = db.Column(db.Text, nullable=False)
    side_effects = db.Column(db.Text, default=None)
    substitutes = db.Column(db.String(30), default=None)


# class Post(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     title = db.Column(db.String(100), nullable=False)
#     date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
#     content = db.Column(db.Text, nullable=False)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

#     def __repr__(self):
#         return f"Post('{self.title}', '{self.date_posted}')"