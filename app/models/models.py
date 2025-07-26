from dataclasses import dataclass
from typing import Optional

from app.conf.db_conf import db


@dataclass
class MenuItem:
    category: str
    name: str
    size: str
    price: float
    photo: str
    item_id: int
    description: str
    available: bool
    isBestSeller: bool


@dataclass
class ExtraIngr:
    name: str
    photo: str
    price: float
    size: str
    available: bool


@dataclass
class OrderTO:
    items: list[dict]
    payment_type: str
    notes: str = ""
    id: Optional[int] = None
    order_no: Optional[int] = None
    type: Optional[str] = None
    tel: Optional[str] = None
    amount_paid: Optional[float] = None
    user_id: Optional[str] = None
    address: Optional[str] = None
    items: Optional[list[dict]] = None
    payment_type: Optional[str] = None


class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.String, unique=True, nullable=False)
    telephone_no = db.Column(db.String, primary_key=True, nullable=False)
    name = db.Column(db.String)
    address = db.Column(db.String)
    amount_of_orders = db.Column(db.Integer, default=0)
    amount_paid = db.Column(db.Float, default=0.0)
    last_order = db.Column(db.String, nullable=True)
    waiting_for_name = db.Column(db.Integer, nullable=True)


class MenuItem(db.Model):
    __tablename__ = "menu_items"

    id = db.Column(db.BigInteger, primary_key=True)
    category = db.Column(db.String)
    name = db.Column(db.String)
    size = db.Column(db.String)
    price = db.Column(db.Float)
    photo = db.Column(db.String)
    description = db.Column(db.String)
    available = db.Column(db.Boolean, default=True)
    is_best_seller = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "category": self.category,
            "name": self.name,
            "size": self.size,
            "price": self.price,
            "photo": self.photo,
            "description": self.description,
            "available": self.available,
            "is_best_seller": self.is_best_seller,
        }


class ExtraIngr(db.Model):
    __tablename__ = "extra_ingr"

    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String)
    photo = db.Column(db.String)
    price = db.Column(db.Float)
    size = db.Column(db.String)
    available = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "photo": self.photo,
            "price": self.price,
            "size": self.size,
            "available": self.available
        }


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.BigInteger, primary_key=True)
    order_no = db.Column(db.Integer)
    telephone_no = db.Column(db.String, db.ForeignKey("customers.telephone_no"), nullable=True)
    status = db.Column(db.String)
    created_at = db.Column(db.DateTime)
    type = db.Column(db.String)
    amount_paid = db.Column(db.Float)
    notes = db.Column(db.String)
    address = db.Column(db.String)
    payment_type = db.Column(db.String)

    items = db.relationship("OrderItem", backref="order", lazy="joined")

    customer = db.relationship(
        "Customer",
        backref="orders",
        primaryjoin="Order.telephone_no == Customer.telephone_no",
        lazy="joined",
        uselist=False,
    )


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.BigInteger, primary_key=True)
    order_id = db.Column(db.BigInteger, db.ForeignKey('orders.id'))
    name = db.Column(db.String)
    quantity = db.Column(db.Integer)
    amount = db.Column(db.Float)
    size = db.Column(db.String)
    category = db.Column(db.String)
    is_garlic_crust = db.Column(db.Boolean)
    is_thin_dough = db.Column(db.Boolean)
    description = db.Column(db.String)
    discount_amount = db.Column(db.Float)