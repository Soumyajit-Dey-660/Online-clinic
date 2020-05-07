from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from hospital import db, login_manager, app
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True)
    doctor_id = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return f"User('{self.id}', '{self.user_id}', '{self.doctor_id}')"


class NormalUser(db.Model, UserMixin):
    id = db.Column(db.Integer, db.ForeignKey('user.user_id'), autoincrement=True, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    appointments = db.relationship('Appointment', backref='author', lazy=True)

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


class DoctorUser(db.Model, UserMixin):
    id = db.Column(db.Integer, db.ForeignKey('user.doctor_id'), autoincrement=True, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
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
    booked_for = db.Column()
    doctor_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('normal_user.id'), nullable=False)


# class Post(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     title = db.Column(db.String(100), nullable=False)
#     date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
#     content = db.Column(db.Text, nullable=False)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

#     def __repr__(self):
#         return f"Post('{self.title}', '{self.date_posted}')"