# 🛍️ AMAZONE - Flask E-Commerce Web App

Welcome to **AMAZONE**, a modern and feature-rich e-commerce web application built using **Flask**, **MySQL**, and **PythonAnywhere** for deployment.

This project simulates a full e-commerce experience: user registration, login, shopping cart, admin stock management, fake checkout, and transaction history – all with modern UI design inspired by Amazon.

---

## 🚀 Features

- 🧑 User Registration & Login
- 🔐 Secure Password Storage
- 📦 Product Listings with Stock Control
- 🛒 AJAX-powered Add-to-Cart Modal
- 🔄 Dynamic Stock Update after Purchase
- 🧾 Order History per User
- 🧑‍💼 Admin Restock Portal
- 💳 Fake Payment Gateway UI
- 📃 Order Success Confirmation
- 🎨 Premium UI Styling (Inspired by Amazon.ca)

---

## 🖼️ Pages

| Page                | Description                                               |
|---------------------|-----------------------------------------------------------|
| `/` or `/products`  | Product catalog with stock, price, and add-to-cart button |
| `/cart`             | Modern cart layout with item quantity updates             |
| `/payment`          | Fake credit card checkout page with address shown         |
| `/order_success/<id>` | Thank you page with order number and continue shopping    |
| `/transaction_history` | View all past orders with clear history option          |
| `/admin/restock`    | Admin restock all items                                   |
| `/login` & `/register` | Auth pages with styled forms                            |

---

## 🧑‍💻 Tech Stack

- **Backend**: Flask (Python)
- **Database**: MySQL (hosted on PythonAnywhere)
- **Frontend**: HTML, CSS (custom), JavaScript (AJAX for modal/cart)
- **Deployment**: PythonAnywhere
- **Authentication**: Session-based login

---

## 📁 Folder Structure

```
.
├── static/
│   ├── css/
│   ├── images/
│   └── scripts/
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── cart.html
│   ├── payment.html
│   ├── login.html
│   ├── register.html
│   ├── order_success.html
│   └── transaction_history.html
├── app.py
├── README.md
└── .gitignore
```

---

## 🛠️ Setup Instructions (Local)

> **Note**: For local MySQL setup, credentials will differ.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/mystore.git
   cd mystore
   ```

2. **Create virtual environment & activate:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Update your MySQL DB credentials in `app.py`**

5. **Run the app:**
   ```bash
   flask run
   ```

---

## 🛡️ Security Notes

- This is a simulation project. Payment is not real.
- All credit card info entered is discarded and not stored or processed.
- Passwords are securely hashed before storage.
- The app is not production-hardened. Do not deploy without security reviews.

---

## 🙌 Credits

Designed & developed by **AOD**, built for educational purposes.  
Modern UI styled manually & inspired by **Amazon.ca**'s interface.

---

## 📄 License

This project is open source under the [MIT License](LICENSE).
```

---