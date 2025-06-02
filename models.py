from . import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    # Relazione con UserBalance
    balance = db.relationship('UserBalance', backref='user', uselist=False)
    # Relazione con ReportOrder
    orders = db.relationship('ReportOrder', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.email}>'

class UserBalance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    balance = db.Column(db.Integer, default=0, nullable=False)

    def __repr__(self):
        return f'<UserBalance UserID: {self.user_id}, Balance: {self.balance}>'

class ReportOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(255), unique=True, nullable=False) # ID transazione Stripe
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<ReportOrder OrderID: {self.order_id}, UserID: {self.user_id}, Quantity: {self.quantity}>'