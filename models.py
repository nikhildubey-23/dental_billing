from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    hsn_code = db.Column(db.String(20), default="")
    price = db.Column(db.Float, nullable=False, default=0.0)
    gst_rate = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "hsn_code": self.hsn_code,
            "price": self.price,
            "gst_rate": self.gst_rate,
        }


class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), default="")
    email = db.Column(db.String(200), default="")
    address = db.Column(db.Text, default="")
    gstin = db.Column(db.String(50), default="")
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "gstin": self.gstin,
        }


def get_next_bill_number():
    last = Bill.query.order_by(Bill.id.desc()).first()
    if last:
        num = int(last.bill_number.split("-")[1]) + 1
    else:
        num = 1
    return f"BILL-{num:04d}"


class Bill(db.Model):
    __tablename__ = "bills"

    id = db.Column(db.Integer, primary_key=True)
    bill_number = db.Column(db.String(20), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=True)
    customer_name = db.Column(db.String(200), default="")
    customer_phone = db.Column(db.String(20), default="")
    customer_address = db.Column(db.Text, default="")
    customer_gstin = db.Column(db.String(50), default="")
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    gst_total = db.Column(db.Float, nullable=False, default=0.0)
    grand_total = db.Column(db.Float, nullable=False, default=0.0)
    is_gst = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    customer = db.relationship("Customer", backref="bills", lazy=True)
    items = db.relationship(
        "BillItem", backref="bill", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "bill_number": self.bill_number,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "customer_phone": self.customer_phone,
            "customer_address": self.customer_address,
            "customer_gstin": self.customer_gstin,
            "subtotal": self.subtotal,
            "gst_total": self.gst_total,
            "grand_total": self.grand_total,
            "is_gst": self.is_gst,
            "created_at": self.created_at.isoformat(),
            "items": [item.to_dict() for item in self.items],
        }


class BillItem(db.Model):
    __tablename__ = "bill_items"

    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey("bills.id"), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    hsn_code = db.Column(db.String(20), default="")
    quantity = db.Column(db.Float, nullable=False, default=1)
    price = db.Column(db.Float, nullable=False, default=0.0)
    gst_rate = db.Column(db.Float, nullable=False, default=0.0)
    gst_amount = db.Column(db.Float, nullable=False, default=0.0)
    total = db.Column(db.Float, nullable=False, default=0.0)

    def to_dict(self):
        return {
            "id": self.id,
            "product_name": self.product_name,
            "hsn_code": self.hsn_code,
            "quantity": self.quantity,
            "price": self.price,
            "gst_rate": self.gst_rate,
            "gst_amount": self.gst_amount,
            "total": self.total,
        }
