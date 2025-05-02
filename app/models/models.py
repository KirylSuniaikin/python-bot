from dataclasses import dataclass
from typing import List


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
class Order:
    order_no: str
    telephone_no: str
    status: str
    date_and_time: str
    type: str
    address: str
    amount_paid: float
    payment_type: str
    notes: str = ""


@dataclass
class OrderItem:
    order_no: str
    id: str
    name: str
    quantity: int
    amount: float
    size: str
    category: str
    isGarlicCrust: bool
    isThinDough: bool
    description: str
    sale_amount: float


@dataclass
class Check:
    order_id: str
    total: float
    items: List[OrderItem]
    date: str


@dataclass
class OrderTO:
    type: str
    tel: str
    amount_paid: float
    user_id: str
    items: list[dict]
    payment_type: str
    notes: str = ""


@dataclass
class Customer:
    id: str
    telephone_no: str
    name: str
    address: str
    amount_of_orders: int
    amount_paid: float
    last_order: str
