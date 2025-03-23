import requests
import random
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors  
from werkzeug.security import generate_password_hash, check_password_hash
from flask import flash
from flask import jsonify
from datetime import datetime


app = Flask(__name__)

# ✅ Secure secret key
app.config['SECRET_KEY'] = '3322c2e1203a075eb7e8b668c1198b3e4876dd02ac8fb4cd4810fdace2d24a4a'

# ✅ MySQL Configuration
app.config['MYSQL_HOST'] = 'Envy123.mysql.pythonanywhere-services.com'
app.config['MYSQL_USER'] = 'Envy123'
app.config['MYSQL_PASSWORD'] = 'Pa$$w0rd2025'  
app.config['MYSQL_DB'] = 'Envy123$Amazone'

mysql = MySQL(app)

# ------------------ USER AUTHENTICATION -------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ""

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        address = request.form.get('address')
        password = request.form.get('password')

        if not name or not email or not address or not password:
            msg = "All fields are required!"
            return render_template('register.html', msg=msg)  # 🔥 Make sure to return a response

        hashed_pw = generate_password_hash(password)

        cur = mysql.connection.cursor()
        cur.execute("SELECT UserID FROM User WHERE Email=%s", (email,))
        existing_user = cur.fetchone()

        if existing_user:
            msg = "Account already exists!"
        else:
            cur.execute("INSERT INTO User (Name, Email, Address, Password) VALUES (%s, %s, %s, %s)", 
                        (name, email, address, hashed_pw))
            mysql.connection.commit()
            cur.close()
            return redirect(url_for('login'))  # ✅ Redirect to login after success

        cur.close()

    return render_template('register.html', msg=msg)  # ✅ Always return a response


@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ""

    if request.method == 'POST':
        username = request.form.get('username')  # ✅ Match form field
        password = request.form.get('password')


        if not username or not password:
            msg = "All fields are required!"
            return render_template('login.html', msg=msg)

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT UserID, Name, Password FROM User WHERE Name=%s", (username,))  # ✅ Match field name
        user = cur.fetchone()
        cur.close()

        if user:
            stored_password = user["Password"]
            print(f"Stored Hash: {stored_password}")  # ✅ Debugging

            if check_password_hash(stored_password, password):
                print("✅ Password matches!")
                session['loggedin'] = True
                session['user_id'] = user["UserID"]
                session['username'] = user["Name"]
                return redirect(url_for('products'))
            else:
                print("❌ Password does NOT match!")
                msg = "Incorrect username or password."
        else:
            print("❌ User not found!")
            msg = "User not found."

    return render_template('login.html', msg=msg)



@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

# -------------------------- PRODUCTS -----------------------------------

@app.route('/fetch_products')
def fetch_products():
    res = requests.get('https://fakestoreapi.com/products')
    products = res.json()

    cur = mysql.connection.cursor()

    for product in products:
        cur.execute("SELECT COUNT(*) FROM Item WHERE Name=%s", (product['title'],))
        count = cur.fetchone()[0]

        if count == 0:
            cur.execute(
                "INSERT INTO Item (Name, Description, Price, Stock, ImageURL) VALUES (%s, %s, %s, %s, %s)",
                (product['title'], product['description'], product['price'], random.randint(5, 20), product['image'])
            )

    mysql.connection.commit()
    cur.close()
    return "Products stored in database"

@app.route('/')
@app.route('/products')
def products():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  # Use DictCursor for dictionaries
    cur.execute("SELECT * FROM Item")
    product_list = cur.fetchall()
    cur.close()

    print("Product List:", product_list)  # Debugging line

    if not product_list:
        print("❌ No products found in the database!")
        return "No products available."

    return render_template('index.html', products=product_list)




# ----------------------- CART FUNCTIONALITY ----------------------------
@app.route('/add_to_cart/<int:pid>', methods=['POST'])
def add_to_cart(pid):
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    quantity = request.form.get('quantity', type=int, default=1)

    cur = mysql.connection.cursor()

    # Fetch current stock
    cur.execute("SELECT Stock FROM Item WHERE ItemID=%s", (pid,))
    stock_result = cur.fetchone()
    if not stock_result:
        return jsonify({"error": "Item not found"}), 400
    stock = stock_result[0]

    # Fetch current quantity in cart
    cur.execute("SELECT Quantity FROM Cart WHERE UserID=%s AND ItemID=%s", (user_id, pid))
    result = cur.fetchone()
    cart_quantity = result[0] if result else 0

    if quantity + cart_quantity > stock:
        remaining = stock - cart_quantity
        error_msg = f"Only {remaining if remaining > 0 else 0} items available!"
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"error": error_msg}), 400
        else:
            flash(error_msg, "error")
            return redirect(url_for('products'))

    # Add or update cart
    if result:
        cur.execute("UPDATE Cart SET Quantity = Quantity + %s WHERE UserID=%s AND ItemID=%s",
                    (quantity, user_id, pid))
    else:
        cur.execute("INSERT INTO Cart(UserID, ItemID, Quantity) VALUES (%s, %s, %s)",
                    (user_id, pid, quantity))

    mysql.connection.commit()
    cur.close()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            "message": "Item added to cart!",
            "new_stock": stock - (quantity + cart_quantity),
            "sold_out": (stock - (quantity + cart_quantity)) == 0
        })
    else:
        flash("Item added to cart!", "success")
        return redirect(url_for('products'))





@app.route('/update_cart/<int:cart_id>', methods=['POST'])
def update_cart(cart_id):
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    new_quantity = int(request.form.get('quantity'))
    user_id = session['user_id']

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Fetch cart and item info
    cur.execute("""
        SELECT Cart.Quantity AS CurrentQuantity, Item.Stock, Item.ItemID
        FROM Cart
        JOIN Item ON Cart.ItemID = Item.ItemID
        WHERE Cart.CartID = %s AND Cart.UserID = %s
    """, (cart_id, user_id))
    
    item = cur.fetchone()
    if not item:
        flash("Item not found in cart.", "error")
        return redirect(url_for('cart'))

    item_id = item["ItemID"]
    current_quantity = item["CurrentQuantity"]
    item_stock = item["Stock"]

    # ✅ Check if new_quantity > available stock
    if new_quantity > item_stock:
        flash(f"Cannot update: Only {item_stock} items available!", "error")
        return redirect(url_for('cart'))

    if new_quantity < 1:
        cur.execute("DELETE FROM Cart WHERE CartID = %s", (cart_id,))
        flash("Item removed from cart!", "success")
    else:
        cur.execute("UPDATE Cart SET Quantity = %s WHERE CartID = %s", (new_quantity, cart_id))
        flash("Cart updated successfully!", "success")

    mysql.connection.commit()
    cur.close()
    return redirect(url_for('cart'))





@app.route('/remove_from_cart/<int:cart_id>', methods=['GET'])
def remove_from_cart(cart_id):
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    cur = mysql.connection.cursor()

    cur.execute("DELETE FROM Cart WHERE CartID = %s AND UserID = %s", (cart_id, user_id))

    mysql.connection.commit()
    cur.close()

    flash("Item removed from cart!", "success")
    return redirect(url_for('cart'))




@app.route('/cart')
def cart():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # ✅ Fix: Include Item.Stock in the query so Jinja2 can access it
    cur.execute("""
        SELECT Cart.CartID, Item.ItemID, Item.Name, Item.Price, Item.ImageURL, Cart.Quantity, Item.Stock
        FROM Cart
        JOIN Item ON Cart.ItemID = Item.ItemID
        WHERE Cart.UserID = %s
    """, (user_id,))

    items = cur.fetchall()
    cur.close()

    total_price = sum(item['Price'] * item['Quantity'] for item in items)

    return render_template('cart.html', items=items, total=total_price)

# ----------------------- PAYMENT FUNCTIONALITY ----------------------------
from datetime import datetime

@app.route('/payment')
def payment():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    cur = mysql.connection.cursor()
    cur.execute("SELECT Address FROM User WHERE UserID=%s", (user_id,))
    user_address = cur.fetchone()[0]
    cur.close()

    return render_template("payment.html", user_address=user_address, current_year=datetime.now().year)


@app.route('/pay', methods=['POST'])
def pay():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    # Fake validation (already handled by pattern in HTML)
    name = request.form.get('name')
    card = request.form.get('card')
    cvc = request.form.get('cvc')
    month = request.form.get('expiry_month')
    year = request.form.get('expiry_year')

    cur = mysql.connection.cursor()

    # 🔢 Step 1: Generate unique 4-digit OrderNumber
    order_number = random.randint(1000, 9999)
    cur.execute("SELECT OrderNumber FROM `Order`")
    existing_numbers = [row[0] for row in cur.fetchall()]
    while order_number in existing_numbers:
        order_number = random.randint(1000, 9999)

    # 📦 Step 2: Create Order with generated OrderNumber
    cur.execute("""
        INSERT INTO `Order` (UserID, OrderNumber, SourceAddress, DestinationAddress)
        VALUES (%s, %s, %s, (SELECT Address FROM User WHERE UserID = %s))
    """, (user_id, order_number, "Amazone Fulfillment Warehouse, Toronto, ON", user_id))
    mysql.connection.commit()

    # Step 3: Get new OrderID
    order_id = cur.lastrowid

    # Step 4: Transfer cart items to OrderContents
    cur.execute("SELECT * FROM Cart WHERE UserID=%s", (user_id,))
    cart_items = cur.fetchall()
    for item in cart_items:
        cur.execute("INSERT INTO OrderContents (OrderID, ItemID, Quantity) VALUES (%s, %s, %s)",
                    (order_id, item[2], item[3]))  # assuming (CartID, UserID, ItemID, Quantity)

    # Step 5: Create Payment record
    cur.execute("""
        INSERT INTO Payment (OrderID, Status, PaymentMethod, TransactionDate)
        VALUES (%s, %s, %s, %s)
    """, (order_id, 'Completed', 'Credit Card', datetime.now()))
    
    # Deduct stock from items properly now
    for item in cart_items:
        item_id = item[2]
        quantity = item[3]
        cur.execute("UPDATE Item SET Stock = Stock - %s WHERE ItemID = %s", (quantity, item_id))


    # Step 6: Clear Cart
    cur.execute("DELETE FROM Cart WHERE UserID=%s", (user_id,))
    mysql.connection.commit()
    cur.close()

    return redirect(url_for('order_success', order_id=order_id))


@app.route('/order_success/<int:order_id>')
def order_success(order_id):
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    return render_template('order_success.html', order_id=order_id)


# ----------------------- TRANSACTION FUNCTIONALITY ----------------------------

@app.route('/transaction_history')
def transaction_history():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # ✅ Only fetch orders with valid payments (no null OrderID in Payment)
    cur.execute("""
        SELECT o.OrderID, o.DestinationAddress, p.Status AS PaymentStatus, p.TransactionDate
        FROM `Order` o
        INNER JOIN Payment p ON o.OrderID = p.OrderID
        WHERE o.UserID = %s
        ORDER BY p.TransactionDate DESC
    """, (user_id,))
    orders = cur.fetchall()

    # ✅ Attach each order's item list
    for order in orders:
        cur.execute("""
            SELECT i.Name AS ItemName, oc.Quantity
            FROM OrderContents oc
            JOIN Item i ON oc.ItemID = i.ItemID
            WHERE oc.OrderID = %s
        """, (order["OrderID"],))
        order["Items"] = cur.fetchall()

    cur.close()
    return render_template("transaction_history.html", orders=orders)

@app.route('/clear_my_transactions', methods=['POST'])
def clear_my_transactions():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    cur = mysql.connection.cursor()

    # ✅ Corrected table name from Orders ➜ Order
    cur.execute("SELECT OrderID FROM `Order` WHERE UserID = %s", (user_id,))
    orders = cur.fetchall()
    order_ids = [order[0] for order in orders]

    if order_ids:
        cur.execute("DELETE FROM Payment WHERE OrderID IN %s", (order_ids,))
        cur.execute("DELETE FROM OrderContents WHERE OrderID IN %s", (order_ids,))
        cur.execute("DELETE FROM `Order` WHERE UserID = %s", (user_id,))

    mysql.connection.commit()
    cur.close()

    flash("Your transaction history has been cleared.", "success")
    return redirect(url_for('cart'))


# ----------------------- ADMIN FUNCTIONALITY ----------------------------
@app.route('/admin/restock', methods=['POST'])
def restock_items():
    if 'loggedin' not in session or session['username'] != 'Admin':
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()

    # Randomly assign stock between 1 and 30 per item
    cur.execute("SELECT ItemID FROM Item")
    items = cur.fetchall()

    for item in items:
        new_stock = random.randint(1, 30)
        cur.execute("UPDATE Item SET Stock = %s WHERE ItemID = %s", (new_stock, item[0]))

    mysql.connection.commit()
    cur.close()

    flash("All items have been restocked randomly!", "success")
    return redirect(url_for('products'))


# ----------------------- RUN FLASK APPLICATION -------------------------

if __name__ == '__main__':
    app.run(debug=True)
