from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from hospital import db, login_manager, app
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    if user is None:
        user = Doctor.query.get(int(user_id))
        if user is None:
            user = Admin.query.get(int(user_id))
    return user


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    address = db.Column(db.String(80), nullable=False)
    state = db.Column(db.String(20), nullable=False)
    city = db.Column(db.String(20), nullable=False)
    zipcode = db.Column(db.String(8), nullable=False)
    phone_number = db.Column(db.String(12), unique=True, nullable=False)
    appointments = db.relationship('Appointment', backref='user', lazy=True)
    eprescriptions = db.relationship('Eprescription', backref='user', lazy=True)
    carts = db.relationship('Cart', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)

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
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"


class Doctor(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    description = db.Column(db.Text, nullable=False)
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
        return Doctor.query.get(user_id)

    def __repr__(self):
        return f"Doctor('{self.username}', '{self.email}', '{self.image_file}')"


class Admin(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    announcements = db.relationship('Announcement', backref='admin', lazy=True)

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
        return Admin.query.get(user_id)

    def __repr__(self):
        return f"Admin({self.username})"


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booked_on = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    booked_for = db.Column(db.DateTime, nullable=False)
    booked_for_time = db.Column(db.String(15), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Appointment('{self.booked_on}' with id '{self.id}')"


class Timing(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('doctor.id'), primary_key=True)
    monday = db.Column(db.String(50), default=None)
    tuesday = db.Column(db.String(50), default=None)
    wednesday = db.Column(db.String(50), default=None)
    thursday = db.Column(db.String(50), default=None)
    friday = db.Column(db.String(50), default=None)
    saturday = db.Column(db.String(50), default=None)
    sunday = db.Column(db.String(50), default=None)

    def __repr__(self):
        return f"Timing('Monday {self.monday}', 'Tuesday {self.tuesday}', 'Wednesday {self.wednesday}',\
                             'Thursday {self.thursday}', 'Friday {self.friday}', 'Saturday {self.saturday}', 'Sunday {self.sunday}')"

class Eprescription(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('appointment.id'), primary_key=True)
    content = db.Column(db.Text(), default=None)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Eprescription('Content {self.content}' for id {self.id})"


class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(40), nullable=False)
    disease = db.Column(db.String(20), nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    manufactured_by = db.Column(db.String(40), nullable=False)
    price = db.Column(db.Float, default=None)
    stock = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    uses = db.Column(db.Text, nullable=False)
    side_effects = db.Column(db.Text, default=None)
    substitutes = db.Column(db.String(30), default=None)
    stock = db.Column(db.Integer, default=100)
    carts = db.relationship('Cartitem', backref='medicine', lazy=True)


    def __repr__(self):
        return f"Medicine('{self.name}' for {self.disease})"


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    cartitems = db.relationship('Cartitem', backref='cart', lazy=True)


class Cartitem(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'))
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicine.id'))
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"CartItem('id  {self.id}', cart_id {self.cart_id})"


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bill_amount = db.Column(db.Float, nullable=False)
    ordered_on = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ordereditems = db.relationship('Ordereditem', backref='order', lazy=True)

    def __repr__(self):
        return f"Order(id {self.id} with total_amount {self.bill_amount})"


class Ordereditem(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    medicine_name = db.Column(db.String(30), nullable=False)
    medicine_image = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)


class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    created_on = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    message = db.Column(db.String(200), nullable=False)
    username = db.Column(db.String(20), nullable=False) 
    room = db.Column(db.String(15), nullable=False)
    sent_on = db.Column(db.DateTime, nullable=False)

# class Post(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     title = db.Column(db.String(100), nullable=False)
#     date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
#     content = db.Column(db.Text, nullable=False)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

#     def __repr__(self):
#         return f"Post('{self.title}', '{self.date_posted}')"