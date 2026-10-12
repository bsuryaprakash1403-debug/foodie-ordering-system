from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from pathlib import Path
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "change-this-secret-key-before-deployment"
DB_PATH = Path(__file__).with_name("food_ordering.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS foods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            price REAL NOT NULL CHECK(price >= 0),
            category TEXT NOT NULL DEFAULT 'Main Course',
            image_url TEXT NOT NULL DEFAULT '',
            available INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            customer_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            total REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Placed',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            food_id INTEGER,
            food_name TEXT NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
            FOREIGN KEY(food_id) REFERENCES foods(id) ON DELETE SET NULL
        );
        """)
        count = db.execute("SELECT COUNT(*) FROM foods").fetchone()[0]
        if count == 0:
            sample_foods = [
                ("Chicken Biriyani", "Aromatic biriyani served with onion raita.", 160, "Biriyani", "https://images.unsplash.com/photo-1563379091339-03246963d96c?w=800"),
                ("Veg Fried Rice", "Stir-fried rice with fresh vegetables.", 110, "Rice", "https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=800"),
                ("Masala Dosa", "Crispy dosa with potato masala and chutneys.", 75, "South Indian", "https://images.unsplash.com/photo-1668236543090-82eba5ee5976?w=800"),
                ("Paneer Butter Masala", "Paneer in a creamy tomato gravy.", 180, "Curry", "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=800"),
                ("Veg Burger", "Vegetable patty with lettuce and sauce.", 90, "Fast Food", "https://images.unsplash.com/photo-1520072959219-c595dc870360?w=800"),
                ("French Fries", "Golden, crispy potato fries.", 65, "Sides", "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=800"),
                ("Chocolate Brownie", "Chocolate brownie for dessert.", 80, "Dessert", "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=800"),
                ("Fresh Lime Juice", "Refreshing lime drink.", 45, "Drinks", "https://images.unsplash.com/photo-1513558161293-cd6d2f2a4f0b?w=800"),
            ]
            db.executemany("INSERT INTO foods(name,description,price,category,image_url) VALUES(?,?,?,?,?)", sample_foods)
        admin = db.execute("SELECT id FROM users WHERE email=?", ("admin@foodie.local",)).fetchone()
        if not admin:
            db.execute("INSERT INTO users(name,email,password_hash,is_admin) VALUES(?,?,?,1)",
                       ("Administrator", "admin@foodie.local", generate_password_hash("Admin@123")))
        db.commit()

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to continue.", "info")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Administrator access is required.", "error")
            return redirect(url_for("index"))
        return view(*args, **kwargs)
    return wrapped

@app.context_processor
def inject_cart_count():
    return {"cart_count": sum(session.get("cart", {}).values())}

@app.route("/")
def index():
    search = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    with get_db() as db:
        categories = [r["category"] for r in db.execute("SELECT DISTINCT category FROM foods WHERE available=1 ORDER BY category")]
        sql = "SELECT * FROM foods WHERE available=1"
        args = []
        if search:
            sql += " AND (name LIKE ? OR description LIKE ?)"
            args.extend([f"%{search}%", f"%{search}%"])
        if category:
            sql += " AND category=?"
            args.append(category)
        sql += " ORDER BY category, name"
        foods = db.execute(sql, args).fetchall()
    return render_template("index.html", foods=foods, categories=categories, search=search, selected_category=category)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 6:
            flash("Enter your name, a valid email, and a password with at least 6 characters.", "error")
            return render_template("register.html")
        try:
            with get_db() as db:
                db.execute("INSERT INTO users(name,email,password_hash) VALUES(?,?,?)",
                           (name, email, generate_password_hash(password)))
                db.commit()
            flash("Account created. You can now sign in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("That email address is already registered.", "error")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["is_admin"] = bool(user["is_admin"])
            session["cart"] = {}
            flash(f"Welcome, {user['name']}!", "success")
            return redirect(url_for("admin_dashboard" if user["is_admin"] else "index"))
        flash("Incorrect email or password.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have signed out.", "info")
    return redirect(url_for("index"))

@app.route("/cart/add/<int:food_id>", methods=["POST"])
def add_to_cart(food_id):
    with get_db() as db:
        food = db.execute("SELECT id FROM foods WHERE id=? AND available=1", (food_id,)).fetchone()
    if not food:
        flash("This item is not available.", "error")
        return redirect(url_for("index"))
    cart = session.get("cart", {})
    key = str(food_id)
    cart[key] = min(int(cart.get(key, 0)) + 1, 99)
    session["cart"] = cart
    flash("Item added to your cart.", "success")
    return redirect(request.referrer or url_for("index"))

@app.route("/cart")
def cart():
    cart_data = session.get("cart", {})
    items, total = [], 0
    if cart_data:
        with get_db() as db:
            for food_id, quantity in cart_data.items():
                food = db.execute("SELECT * FROM foods WHERE id=? AND available=1", (int(food_id),)).fetchone()
                if food:
                    line_total = food["price"] * int(quantity)
                    items.append({"food": food, "quantity": int(quantity), "line_total": line_total})
                    total += line_total
    return render_template("cart.html", items=items, total=total)

@app.route("/cart/update", methods=["POST"])
def update_cart():
    cart_data = session.get("cart", {})
    for food_id in list(cart_data.keys()):
        try:
            quantity = int(request.form.get(f"quantity_{food_id}", cart_data[food_id]))
        except ValueError:
            quantity = 1
        if quantity <= 0:
            cart_data.pop(food_id, None)
        else:
            cart_data[food_id] = min(quantity, 99)
    session["cart"] = cart_data
    flash("Cart updated.", "success")
    return redirect(url_for("cart"))

@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    cart_data = session.get("cart", {})
    if not cart_data:
        flash("Your cart is empty.", "info")
        return redirect(url_for("index"))
    items, total = [], 0
    with get_db() as db:
        for food_id, quantity in cart_data.items():
            food = db.execute("SELECT * FROM foods WHERE id=? AND available=1", (int(food_id),)).fetchone()
            if food:
                quantity = int(quantity)
                items.append((food, quantity))
                total += food["price"] * quantity
    if not items:
        flash("Your cart has no available items.", "error")
        return redirect(url_for("cart"))
    if request.method == "POST":
        customer_name = request.form.get("customer_name", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        if not customer_name or not phone or not address:
            flash("Please complete all delivery details.", "error")
            return render_template("checkout.html", items=items, total=total)
        with get_db() as db:
            cursor = db.execute(
                "INSERT INTO orders(user_id,customer_name,phone,address,total) VALUES(?,?,?,?,?)",
                (session["user_id"], customer_name, phone, address, total))
            order_id = cursor.lastrowid
            for food, quantity in items:
                db.execute("INSERT INTO order_items(order_id,food_id,food_name,price,quantity) VALUES(?,?,?,?,?)",
                           (order_id, food["id"], food["name"], food["price"], quantity))
            db.commit()
        session["cart"] = {}
        return redirect(url_for("order_success", order_id=order_id))
    return render_template("checkout.html", items=items, total=total)

@app.route("/order-success/<int:order_id>")
@login_required
def order_success(order_id):
    with get_db() as db:
        order = db.execute("SELECT * FROM orders WHERE id=? AND user_id=?", (order_id, session["user_id"])).fetchone()
    if not order:
        return redirect(url_for("orders"))
    return render_template("order_success.html", order=order)

@app.route("/orders")
@login_required
def orders():
    with get_db() as db:
        order_rows = db.execute("SELECT * FROM orders WHERE user_id=? ORDER BY id DESC", (session["user_id"],)).fetchall()
        order_items = {}
        for order in order_rows:
            order_items[order["id"]] = db.execute("SELECT * FROM order_items WHERE order_id=?", (order["id"],)).fetchall()
    return render_template("orders.html", orders=order_rows, order_items=order_items)

@app.route("/admin")
@login_required
@admin_required
def admin_dashboard():
    with get_db() as db:
        foods = db.execute("SELECT * FROM foods ORDER BY id DESC").fetchall()
        orders = db.execute("""SELECT orders.*, users.name AS account_name, users.email
                               FROM orders JOIN users ON orders.user_id=users.id
                               ORDER BY orders.id DESC""").fetchall()
    return render_template("admin.html", foods=foods, orders=orders)

@app.route("/admin/food/add", methods=["POST"])
@login_required
@admin_required
def add_food():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    category = request.form.get("category", "Main Course").strip() or "Main Course"
    image_url = request.form.get("image_url", "").strip()
    try:
        price = float(request.form.get("price", "0"))
        if price < 0: raise ValueError
    except ValueError:
        flash("Enter a valid non-negative price.", "error")
        return redirect(url_for("admin_dashboard"))
    if not name:
        flash("Food name is required.", "error")
        return redirect(url_for("admin_dashboard"))
    with get_db() as db:
        db.execute("INSERT INTO foods(name,description,price,category,image_url) VALUES(?,?,?,?,?)",
                   (name, description, price, category, image_url))
        db.commit()
    flash("Food item added.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/food/toggle/<int:food_id>", methods=["POST"])
@login_required
@admin_required
def toggle_food(food_id):
    with get_db() as db:
        db.execute("UPDATE foods SET available=CASE available WHEN 1 THEN 0 ELSE 1 END WHERE id=?", (food_id,))
        db.commit()
    flash("Food availability updated.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/order/status/<int:order_id>", methods=["POST"])
@login_required
@admin_required
def update_order_status(order_id):
    status = request.form.get("status", "")
    if status not in {"Placed", "Preparing", "Out for delivery", "Delivered", "Cancelled"}:
        flash("Invalid order status.", "error")
    else:
        with get_db() as db:
            db.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
            db.commit()
        flash("Order status updated.", "success")
    return redirect(url_for("admin_dashboard"))

@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404


# Initialize database when the app starts
init_db()

if __name__ == "__main__":
    app.run(debug=True)

