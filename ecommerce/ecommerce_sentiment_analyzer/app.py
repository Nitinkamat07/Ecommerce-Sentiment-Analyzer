import os
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from sentiment_service import analyze_sentiment, analyze_aspects

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-this-key")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(app.root_path, "shop.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviews = db.relationship("Review", backref="author", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    stock = db.Column(db.Integer, default=20, nullable=False)
    reviews = db.relationship("Review", backref="product", cascade="all, delete-orphan", lazy=True)

    @property
    def average_rating(self):
        values = [r.rating for r in self.reviews]
        return round(sum(values) / len(values), 1) if values else 0

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    body = db.Column(db.Text, nullable=False)
    sentiment = db.Column(db.String(20), nullable=False)
    sentiment_score = db.Column(db.Float, nullable=False, default=0)
    aspects = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint("product_id", "user_id", name="one_review_per_user_product"),)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    total = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship("OrderItem", backref="order", cascade="all, delete-orphan", lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    product_name = db.Column(db.String(140), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def admin_required(fn):
    @wraps(fn)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return fn(*args, **kwargs)
    return wrapped

def sentiment_counts(reviews):
    counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
    for r in reviews:
        counts[r.sentiment] = counts.get(r.sentiment, 0) + 1
    return counts

@app.context_processor
def inject_globals():
    cart = session.get("cart", {})
    return {"cart_count": sum(int(q) for q in cart.values())}

@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    sort = request.args.get("sort", "featured")
    query = Product.query
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))
    if category:
        query = query.filter_by(category=category)
    products = query.all()
    if sort == "price-low":
        products.sort(key=lambda p: p.price)
    elif sort == "price-high":
        products.sort(key=lambda p: p.price, reverse=True)
    elif sort == "rating":
        products.sort(key=lambda p: p.average_rating, reverse=True)
    categories = [c[0] for c in db.session.query(Product.category).distinct().order_by(Product.category).all()]
    return render_template("index.html", products=products, categories=categories, q=q, category=category, sort=sort)

@app.route("/product/<int:product_id>", methods=["GET", "POST"])
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == "POST":
        if not current_user.is_authenticated:
            flash("Please sign in before submitting a review.", "warning")
            return redirect(url_for("login"))
        body = request.form.get("body", "").strip()
        rating = request.form.get("rating", type=int)
        if not body or len(body) < 5 or len(body) > 1200:
            flash("Review must be between 5 and 1,200 characters.", "danger")
        elif rating not in [1, 2, 3, 4, 5]:
            flash("Please select a rating from 1 to 5.", "danger")
        else:
            # One review per account per product: update the existing review if present.
            review = Review.query.filter_by(product_id=product.id, user_id=current_user.id).first()
            label, score = analyze_sentiment(body)
            aspects = ", ".join(analyze_aspects(body))
            if review:
                review.rating = rating
                review.body = body
                review.sentiment = label
                review.sentiment_score = score
                review.aspects = aspects
                review.created_at = datetime.utcnow()
                message = f"Your review was updated and reclassified as {label}."
            else:
                review = Review(product_id=product.id, user_id=current_user.id, rating=rating,
                                body=body, sentiment=label, sentiment_score=score, aspects=aspects)
                db.session.add(review)
                message = f"Review submitted and classified as {label}."
            db.session.commit()
            flash(message, "success")
            return redirect(url_for("product_detail", product_id=product.id))
    existing_review = None
    if current_user.is_authenticated and not current_user.is_admin:
        existing_review = Review.query.filter_by(product_id=product.id, user_id=current_user.id).first()
    counts = sentiment_counts(product.reviews)
    return render_template("product.html", product=product, counts=counts, existing_review=existing_review)

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if len(username) < 3 or len(password) < 8 or "@" not in email:
            flash("Use a username of at least 3 characters, a valid email, and password of at least 8 characters.", "danger")
        elif User.query.filter(func.lower(User.username) == username.lower()).first() or User.query.filter_by(email=email).first():
            flash("Username or email already exists.", "danger")
        else:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Welcome! Your account is ready.", "success")
            return redirect(url_for("index"))
    return render_template("auth.html", mode="register")

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        identity = request.form.get("identity", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter(func.lower(User.username) == identity.lower()).first()
        if not user:
            user = User.query.filter_by(email=identity.lower()).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Signed in successfully.", "success")
            return redirect(url_for("admin_dashboard") if user.is_admin else url_for("index"))
        flash("Invalid username/email or password.", "danger")
    return render_template("auth.html", mode="login")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("index"))

@app.route("/cart")
def cart():
    cart_data = session.get("cart", {})
    items, total = [], 0
    for pid, qty in cart_data.items():
        product = db.session.get(Product, int(pid))
        if product and int(qty) > 0:
            subtotal = product.price * int(qty)
            items.append({"product": product, "quantity": int(qty), "subtotal": subtotal})
            total += subtotal
    return render_template("cart.html", items=items, total=total)

@app.route("/cart/add/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    cart_data = session.get("cart", {})
    key = str(product.id)
    qty = int(cart_data.get(key, 0)) + 1
    if qty > product.stock:
        flash("Sorry, the available stock limit has been reached.", "warning")
    else:
        cart_data[key] = qty
        session["cart"] = cart_data
        flash(f"{product.name} added to your cart.", "success")
    return redirect(request.referrer or url_for("index"))

@app.route("/cart/update", methods=["POST"])
def update_cart():
    cart_data = session.get("cart", {})
    for pid in list(cart_data):
        product = db.session.get(Product, int(pid))
        qty = request.form.get(f"qty_{pid}", type=int)
        if not product or qty is None or qty <= 0:
            cart_data.pop(pid, None)
        else:
            cart_data[pid] = min(qty, product.stock)
    session["cart"] = cart_data
    flash("Cart updated.", "success")
    return redirect(url_for("cart"))

@app.route("/cart/remove/<int:product_id>", methods=["POST"])
def remove_from_cart(product_id):
    cart_data = session.get("cart", {})
    cart_data.pop(str(product_id), None)
    session["cart"] = cart_data
    flash("Item removed from cart.", "success")
    return redirect(url_for("cart"))

@app.route("/checkout", methods=["POST"])
@login_required
def checkout():
    cart_data = session.get("cart", {})
    if not cart_data:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("cart"))
    order = Order(user_id=current_user.id, total=0)
    db.session.add(order)
    total = 0
    for pid, qty in cart_data.items():
        product = db.session.get(Product, int(pid))
        qty = int(qty)
        if not product or qty <= 0 or qty > product.stock:
            db.session.rollback()
            flash("One or more cart items are unavailable. Please review your cart.", "danger")
            return redirect(url_for("cart"))
        order.items.append(OrderItem(product_id=product.id, product_name=product.name,
                                     quantity=qty, unit_price=product.price))
        product.stock -= qty
        total += product.price * qty
    order.total = round(total, 2)
    db.session.commit()
    session["cart"] = {}
    flash(f"Demo order #{order.id} placed successfully. No payment was processed.", "success")
    return redirect(url_for("orders"))

@app.route("/orders")
@login_required
def orders():
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template("orders.html", orders=user_orders)

@app.route("/admin")
@admin_required
def admin_dashboard():
    products = Product.query.order_by(Product.name).all()
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    counts = sentiment_counts(reviews)
    total = len(reviews)
    percentages = {k: round(v * 100 / total, 1) if total else 0 for k, v in counts.items()}
    negative_products = []
    for p in products:
        pc = sentiment_counts(p.reviews)
        n = len(p.reviews)
        if n:
            negative_products.append({"product": p, "negative": pc["Negative"], "total": n,
                                      "percent": round(pc["Negative"] * 100 / n, 1)})
    negative_products.sort(key=lambda x: (x["percent"], x["total"]), reverse=True)
    sentiment_filter = request.args.get("sentiment", "")
    product_filter = request.args.get("product", type=int)
    filtered = reviews
    if sentiment_filter in ["Positive", "Neutral", "Negative"]:
        filtered = [r for r in filtered if r.sentiment == sentiment_filter]
    if product_filter:
        filtered = [r for r in filtered if r.product_id == product_filter]
    chart_labels = [p.name for p in products]
    chart_values = [sentiment_counts(p.reviews) for p in products]
    return render_template("admin.html", products=products, reviews=filtered, counts=counts,
                           percentages=percentages, total=total, negative_products=negative_products[:5],
                           chart_labels=chart_labels, chart_values=chart_values,
                           user_count=User.query.count(), product_count=Product.query.count(),
                           sentiment_filter=sentiment_filter, product_filter=product_filter)

@app.route("/admin/reanalyze", methods=["POST"])
@admin_required
def reanalyze_reviews():
    for review in Review.query.all():
        review.sentiment, review.sentiment_score = analyze_sentiment(review.body)
        review.aspects = ", ".join(analyze_aspects(review.body))
    db.session.commit()
    flash("All reviews have been re-analyzed.", "success")
    return redirect(url_for("admin_dashboard"))

@app.errorhandler(403)
def forbidden(_):
    return render_template("error.html", code=403, message="You do not have permission to access this page."), 403

@app.errorhandler(404)
def not_found(_):
    return render_template("error.html", code=404, message="The page you requested could not be found."), 404

def seed_data():
    if Product.query.count() == 0:
        samples = [
            ("Nova X Smartphone", "Electronics", "A versatile smartphone with a bright display, dependable camera and all-day performance.", 24999, "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9", 18),
            ("Sonic Wireless Headphones", "Electronics", "Comfortable wireless headphones with rich sound and long battery life.", 3499, "https://images.unsplash.com/photo-1505740420928", 35),
            ("Pulse Smart Watch", "Wearables", "Track everyday activity, notifications and workouts with a lightweight smartwatch.", 4999, "https://images.unsplash.com/photo-1523275335684", 22),
            ("Everyday Backpack", "Accessories", "A practical water-resistant backpack with a laptop compartment and multiple pockets.", 1799, "https://images.unsplash.com/photo-1553062407", 30),
            ("Mechanical Keyboard", "Accessories", "A compact mechanical keyboard designed for typing and productivity.", 2899, "https://images.unsplash.com/photo-1587829741301", 16),
            ("Brew Mini Coffee Maker", "Home", "A compact coffee maker for quick coffee at home or in a small office.", 2299, "https://images.unsplash.com/photo-1495474472287", 12),
        ]
        # Replace shortened Unsplash photo identifiers with complete image URLs.
        image_ids = [
            "photo-1511707171634-5f897ff02aa9", "photo-1505740420928", "photo-1523275335684",
            "photo-1553062407", "photo-1587829741301", "photo-1495474472287"
        ]
        full_ids = [
            "photo-1511707171634-5f897ff02aa9", "photo-1505740420928", "photo-1523275335684",
            "photo-1553062407", "photo-1587829741301", "photo-1495474472287"
        ]
        for i, item in enumerate(samples):
            name, category, description, price, image_key, stock = item
            # Valid, generic Unsplash source image URL with a stable photo id.
            urls = [
                "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=900&q=80",
                "https://soniclamb.com/cdn/shop/files/website_gen1.png?v=1788935146&width=823",
                "https://images.unsplash.com/photo-1523275335684?auto=format&fit=crop&w=900&q=80",
                "https://images.unsplash.com/photo-1553062407?auto=format&fit=crop&w=900&q=80",
                "https://images.unsplash.com/photo-1587829741301?auto=format&fit=crop&w=900&q=80",
                "https://images.unsplash.com/photo-1495474472287?auto=format&fit=crop&w=900&q=80",
            ]
            db.session.add(Product(name=name, category=category, description=description,
                                   price=price, image_url=urls[i], stock=stock))
        db.session.commit()
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@shopdemo.local")
    admin_password = os.environ.get("ADMIN_PASSWORD", "Admin123!")
    if not User.query.filter_by(email=admin_email).first():
        admin = User(username="admin", email=admin_email, is_admin=True)
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()

with app.app_context():
    db.create_all()
    seed_data()

if __name__ == "__main__":
    app.run(debug=True)
