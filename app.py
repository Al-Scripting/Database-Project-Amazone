import requests
from flask import Flask, render_template, request, redirect, url_for, session
from flask import Flask
from flask_mysqldb import MySQL
from static.scripts.forms import LoginForm, RegistrationForm  # Import your form classes
from flask import render_template, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask
from flask_mysqldb import MySQL
from flask import Flask, render_template, request, redirect, url_for, session


app = Flask(__name__)

# ✅ Add this secret key to fix the error
app.config['SECRET_KEY'] = '3322c2e1203a075eb7e8b668c1198b3e4876dd02ac8fb4cd4810fdace2d24a4a'  # Replace with a secure key



# MySQL configuration for PythonAnywhere
app.config['MYSQL_HOST'] = 'Envy123.mysql.pythonanywhere-services.com'
app.config['MYSQL_USER'] = 'Envy123'
app.config['MYSQL_PASSWORD'] = 'Pa$$w0rd2025'  # Your MySQL password
app.config['MYSQL_DB'] = 'Envy123$Amazone'  # Replace with your actual database name

mysql = MySQL(app)


@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        hashed_pw = generate_password_hash(password)  # ✅ Ensure password is hashed

        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM users WHERE username=%s", (username,))
        existing_user = cur.fetchone()

        if existing_user:
            msg = "Account already exists!"
        else:
            cur.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", 
                        (username, email, hashed_pw))  # ✅ Store hashed password
            mysql.connection.commit()
            msg = "You have successfully registered!"

        cur.close()
    return render_template('register.html', msg=msg)

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT id, username, password FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        cur.close()

        if user:
            stored_password = user[2]  # Assuming password is the third column
            
            print("Entered Password:", password)
            print("Stored Hash:", stored_password)

            if check_password_hash(stored_password, password):  # ✅ Verify hashed password
                print("✅ Password matches!")
                session['loggedin'] = True
                session['user_id'] = user[0]
                session['username'] = user[1]
                return redirect(url_for('products'))
            else:
                print("❌ Password does NOT match!")
                msg = "Incorrect username or password."
        else:
            msg = "User not found."

    return render_template('login.html', msg=msg)





@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/')
@app.route('/products')
def products():
    # Fetch product list from FakeStoreAPI
    res = requests.get('https://fakestoreapi.com/products')  # Use requests.get()
    product_list = res.json()  # parse JSON into Python list of dicts
    return render_template('index.html', products=product_list)


@app.route('/add_to_cart/<int:pid>')
def add_to_cart(pid):
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    cur = mysql.connection.cursor()
    # Check if this product is already in cart for this user
    cur.execute("SELECT quantity FROM cart WHERE user_id=%s AND product_id=%s", (user_id, pid))
    result = cur.fetchone()
    if result:
        # If already in cart, update quantity (+1)
        cur.execute("UPDATE cart SET quantity = quantity + 1 WHERE user_id=%s AND product_id=%s", (user_id, pid))
    else:
        # If not in cart, insert new record with quantity 1
        cur.execute("INSERT INTO cart(user_id, product_id, quantity) VALUES (%s, %s, %s)", 
                    (user_id, pid, 1))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('cart'))


@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    cur = mysql.connection.cursor()
    # Join cart with products table to get product details (if product table exists)
    cur.execute("""SELECT cart.id, cart.product_id, cart.quantity, products.title, products.price 
                  FROM cart JOIN products ON cart.product_id = products.id 
                  WHERE cart.user_id = %s""", (user_id,))
    items = cur.fetchall()
    cur.close()
    # Calculate total
    total_price = sum(item['price'] * item['quantity'] for item in items)
    return render_template('cart.html', items=items, total=total_price)


# Run Flask Application
if __name__ == '__main__':
    app.run(debug=True)