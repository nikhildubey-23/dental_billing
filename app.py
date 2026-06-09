import os
from datetime import datetime, timezone
from io import BytesIO
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    send_file,
    flash,
)
from config import Config
from models import db, Product, Customer, Bill, BillItem, get_next_bill_number
from utils.pdf_generator import generate_pdf

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

@app.context_processor
def inject_now():
    return {"now": lambda: datetime.now(timezone.utc)}


# ---------- Database Init ----------
_tables_created = False

@app.before_request
def create_tables():
    global _tables_created
    if not _tables_created:
        db.create_all()
        _tables_created = True


# ---------- Dashboard ----------
@app.route("/")
def dashboard():
    total_bills = Bill.query.count()
    total_revenue = db.session.query(db.func.sum(Bill.grand_total)).scalar() or 0
    total_products = Product.query.count()
    total_customers = Customer.query.count()
    recent_bills = (
        Bill.query.order_by(Bill.created_at.desc()).limit(5).all()
    )
    return render_template(
        "dashboard.html",
        total_bills=total_bills,
        total_revenue=total_revenue,
        total_products=total_products,
        total_customers=total_customers,
        recent_bills=recent_bills,
    )


# ---------- Products ----------
@app.route("/products")
def products():
    all_products = Product.query.order_by(Product.name).all()
    return render_template("products.html", products=all_products)


@app.route("/api/products", methods=["GET"])
def api_products():
    products = Product.query.order_by(Product.name).all()
    return jsonify([p.to_dict() for p in products])


@app.route("/api/products", methods=["POST"])
def api_product_add():
    data = request.get_json()
    product = Product(
        name=data["name"],
        hsn_code=data.get("hsn_code", ""),
        price=float(data.get("price", 0)),
        gst_rate=float(data.get("gst_rate", 0)),
    )
    db.session.add(product)
    db.session.commit()
    return jsonify(product.to_dict()), 201


@app.route("/api/products/<int:product_id>", methods=["PUT"])
def api_product_update(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"error": "Not found"}), 404
    data = request.get_json()
    product.name = data.get("name", product.name)
    product.hsn_code = data.get("hsn_code", product.hsn_code)
    product.price = float(data.get("price", product.price))
    product.gst_rate = float(data.get("gst_rate", product.gst_rate))
    db.session.commit()
    return jsonify(product.to_dict())


@app.route("/api/products/<int:product_id>", methods=["DELETE"])
def api_product_delete(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(product)
    db.session.commit()
    return jsonify({"success": True})


# ---------- Customers ----------
@app.route("/customers")
def customers():
    all_customers = Customer.query.order_by(Customer.name).all()
    return render_template("customers.html", customers=all_customers)


@app.route("/api/customers", methods=["GET"])
def api_customers():
    customers = Customer.query.order_by(Customer.name).all()
    return jsonify([c.to_dict() for c in customers])


@app.route("/api/customers", methods=["POST"])
def api_customer_add():
    data = request.get_json()
    customer = Customer(
        name=data["name"],
        phone=data.get("phone", ""),
        email=data.get("email", ""),
        address=data.get("address", ""),
        gstin=data.get("gstin", ""),
    )
    db.session.add(customer)
    db.session.commit()
    return jsonify(customer.to_dict()), 201


@app.route("/api/customers/<int:customer_id>", methods=["PUT"])
def api_customer_update(customer_id):
    customer = db.session.get(Customer, customer_id)
    if not customer:
        return jsonify({"error": "Not found"}), 404
    data = request.get_json()
    customer.name = data.get("name", customer.name)
    customer.phone = data.get("phone", customer.phone)
    customer.email = data.get("email", customer.email)
    customer.address = data.get("address", customer.address)
    customer.gstin = data.get("gstin", customer.gstin)
    db.session.commit()
    return jsonify(customer.to_dict())


@app.route("/api/customers/<int:customer_id>", methods=["DELETE"])
def api_customer_delete(customer_id):
    customer = db.session.get(Customer, customer_id)
    if not customer:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"success": True})


# ---------- Bills ----------
@app.route("/bills/new")
def create_bill():
    products = [p.to_dict() for p in Product.query.order_by(Product.name).all()]
    customers = [c.to_dict() for c in Customer.query.order_by(Customer.name).all()]
    return render_template("create_bill.html", products=products, customers=customers)


@app.route("/bills")
def bills():
    all_bills = Bill.query.order_by(Bill.created_at.desc()).all()
    return render_template("bills.html", bills=all_bills)


@app.route("/api/bills", methods=["POST"])
def api_create_bill():
    data = request.get_json()
    is_gst = data.get("is_gst", False)
    customer_id = data.get("customer_id")

    customer = None
    if customer_id:
        customer = db.session.get(Customer, customer_id)

    bill = Bill(
        bill_number=get_next_bill_number(),
        customer_id=customer.id if customer else None,
        customer_name=customer.name if customer else data.get("customer_name", "Walk-in Customer"),
        customer_phone=customer.phone if customer else data.get("customer_phone", ""),
        customer_address=customer.address if customer else data.get("customer_address", ""),
        customer_gstin=customer.gstin if customer else data.get("customer_gstin", ""),
        subtotal=0,
        gst_total=0,
        grand_total=0,
        is_gst=is_gst,
    )
    db.session.add(bill)
    db.session.flush()

    subtotal = 0
    gst_total = 0

    for item_data in data.get("items", []):
        price = float(item_data.get("price", 0))
        quantity = float(item_data.get("quantity", 1))
        gst_rate = float(item_data.get("gst_rate", 0))

        item_total = price * quantity
        gst_amount = 0
        if is_gst and gst_rate > 0:
            gst_amount = item_total * gst_rate / 100

        db.session.add(
            BillItem(
                bill_id=bill.id,
                product_name=item_data.get("product_name", ""),
                hsn_code=item_data.get("hsn_code", ""),
                quantity=quantity,
                price=price,
                gst_rate=gst_rate,
                gst_amount=gst_amount,
                total=item_total + gst_amount,
            )
        )
        subtotal += item_total
        gst_total += gst_amount

    bill.subtotal = subtotal
    bill.gst_total = gst_total
    bill.grand_total = subtotal + gst_total
    db.session.commit()

    return jsonify(bill.to_dict()), 201


@app.route("/api/bills/<int:bill_id>")
def api_get_bill(bill_id):
    bill = db.session.get(Bill, bill_id)
    if not bill:
        return jsonify({"error": "Not found"}), 404
    return jsonify(bill.to_dict())


@app.route("/bills/<int:bill_id>")
def view_bill(bill_id):
    bill = db.session.get(Bill, bill_id)
    if not bill:
        flash("Bill not found", "error")
        return redirect(url_for("bills"))
    return render_template("bill_preview.html", bill=bill)


@app.route("/bills/<int:bill_id>/pdf")
def download_bill_pdf(bill_id):
    bill = db.session.get(Bill, bill_id)
    if not bill:
        flash("Bill not found", "error")
        return redirect(url_for("bills"))

    pdf = generate_pdf(bill.to_dict())
    return send_file(
        pdf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{bill.bill_number}.pdf",
    )


@app.route("/api/bills/<int:bill_id>", methods=["DELETE"])
def api_delete_bill(bill_id):
    bill = db.session.get(Bill, bill_id)
    if not bill:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(bill)
    db.session.commit()
    return jsonify({"success": True})


@app.route("/api/search")
def api_search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"products": [], "customers": []})

    products = Product.query.filter(Product.name.ilike(f"%{q}%")).limit(10).all()
    customers = Customer.query.filter(Customer.name.ilike(f"%{q}%")).limit(10).all()

    return jsonify({
        "products": [p.to_dict() for p in products],
        "customers": [c.to_dict() for c in customers],
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
