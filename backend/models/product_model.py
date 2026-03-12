from extensions import db

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    description = db.Column(db.Text)
    price = db.Column(db.Float)
    category = db.Column(db.String(100))
    stock = db.Column(db.Integer)