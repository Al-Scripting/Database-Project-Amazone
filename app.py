import requests
import random
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors  
from werkzeug.security import generate_password_hash, check_password_hash
from flask import flash
from flask import jsonify


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
    quantity = request.form.get('quantity', type=int, default=1)  # Ensure quantity is an integer

    cur = mysql.connection.cursor()

    # Get available stock
    cur.execute("SELECT Stock FROM Item WHERE ItemID=%s", (pid,))
    stock_result = cur.fetchone()

    if not stock_result:
        return jsonify({"error": "Item not found"}), 400

    available_stock = stock_result[0]

    if quantity > available_stock:
        return jsonify({"error": f"Only {available_stock} items available!"}), 400

    # Check if item is already in cart
    cur.execute("SELECT Quantity FROM Cart WHERE UserID=%s AND ItemID=%s", (user_id, pid))
    result = cur.fetchone()

    if result:
        current_quantity = result[0]
        if current_quantity + quantity > available_stock:
            return jsonify({"error": f"Only {available_stock} items available!"}), 400

        cur.execute("UPDATE Cart SET Quantity = Quantity + %s WHERE UserID=%s AND ItemID=%s",
                    (quantity, user_id, pid))
    else:
        cur.execute("INSERT INTO Cart(UserID, ItemID, Quantity) VALUES (%s, %s, %s)",
                    (user_id, pid, quantity))

    # Reduce stock in Item table
    cur.execute("UPDATE Item SET Stock = Stock - %s WHERE ItemID=%s", (quantity, pid))

    mysql.connection.commit()
    cur.close()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"message": "Item added to cart!"})

    flash("Item added to cart!", "success")
    return redirect(url_for('cart'))


@app.route('/update_cart/<int:cart_id>', methods=['POST'])
def update_cart(cart_id):
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    new_quantity = int(request.form.get('quantity'))
    user_id = session['user_id']

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Get the current quantity in the cart and item stock
    cur.execute("""
        SELECT Cart.Quantity, Item.Stock, Item.ItemID
        FROM Cart
        JOIN Item ON Cart.ItemID = Item.ItemID
        WHERE Cart.CartID = %s AND Cart.UserID = %s
    """, (cart_id, user_id))
    
    item = cur.fetchone()

    if item:
        current_quantity = item["Quantity"]
        stock = item["Stock"]
        item_id = item["ItemID"]

        if new_quantity < 1:
            # Remove item if quantity is set to zero or below
            cur.execute("DELETE FROM Cart WHERE CartID = %s", (cart_id,))
            cur.execute("UPDATE Item SET Stock = Stock + %s WHERE ItemID = %s", (current_quantity, item_id))
            flash("Item removed from cart!", "success")
        elif new_quantity > stock + current_quantity:
            flash(f"Cannot update: Only {stock + current_quantity} available!", "error")
        else:
            difference = current_quantity - new_quantity
            cur.execute("UPDATE Cart SET Quantity = %s WHERE CartID = %s AND UserID = %s", 
                        (new_quantity, cart_id, user_id))
            cur.execute("UPDATE Item SET Stock = Stock + %s WHERE ItemID = %s", (difference, item_id))
            flash("Cart updated successfully!", "success")

        mysql.connection.commit()
    else:
        flash("Item not found in cart.", "error")

    cur.close()
    return redirect(url_for('cart'))



@app.route('/remove_from_cart/<int:cart_id>', methods=['GET'])
def remove_from_cart(cart_id):
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Get the item being removed
    cur.execute("SELECT ItemID, Quantity FROM Cart WHERE CartID=%s AND UserID=%s", (cart_id, user_id))
    item = cur.fetchone()

    if item:
        item_id = item["ItemID"]
        quantity_removed = item["Quantity"]

        # Restore stock when an item is removed
        cur.execute("UPDATE Item SET Stock = Stock + %s WHERE ItemID=%s", (quantity_removed, item_id))
        cur.execute("DELETE FROM Cart WHERE CartID=%s", (cart_id,))
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

# ----------------------- RUN FLASK APPLICATION -------------------------

if __name__ == '__main__':
    app.run(debug=True)
