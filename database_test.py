import sqlite3
from datetime import datetime
from collections import Counter


# CONNECTIONS TO DB
conn = sqlite3.connect('testdatabase.db')
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys = ON")


# CUSTOMER TABLE
cursor.execute('''
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL
)
''')

# INVENTORY TABLE
cursor.execute('''
CREATE TABLE IF NOT EXISTS inventory (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    color TEXT NOT NULL,
    size TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    description TEXT
)
''')

# ORDERS TABLE
cursor.execute('''
CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    order_date TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
)
''')

# ITEMS ORDERED TABLE
cursor.execute('''
CREATE TABLE IF NOT EXISTS order_items (
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES inventory(product_id),
    PRIMARY KEY (order_id, product_id)
)
''')

conn.commit()





# Add a product to inventory
def add_product(color, size, quantity, description):
    cursor.execute('''
        INSERT INTO inventory (color, size, quantity, description)
        VALUES (?, ?, ?, ?)
    ''', (color, size, quantity, description))
    conn.commit()
    print("Product added to inventory.")


# View all products
def view_all_products():
    cursor.execute('SELECT product_id, color, size, quantity, description FROM inventory')
    products = cursor.fetchall()

    if not products:
        print(" Inventory is empty.")
        return

    print("All Products in Inventory:")
    for p in products:
        print(f"ID {p[0]} | {p[1]} {p[2]} — {p[3]} in stock — {p[4]}")


# Add a new customer
def add_customer(username, password):
    cursor.execute('''
        INSERT INTO customers (username, password)
        VALUES (?, ?)
    ''', (username, password))
    conn.commit()
    print("Customer added.")


# Place an order for a customer
def place_order(customer_id, product_ids):
    product_counts = Counter(product_ids)


    for pid, qty in product_counts.items():
        cursor.execute("SELECT quantity FROM inventory WHERE product_id = ?", (pid,))
        row = cursor.fetchone()
        if not row:
            print(f"Product ID {pid} not found.")
            return
        if row[0] < qty:
            print(f" Not enough stock for Product ID {pid}. Requested: {qty}, Available: {row[0]}")
            return

    order_date = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('''
        INSERT INTO orders (customer_id, order_date)
        VALUES (?, ?)
    ''', (customer_id, order_date))
    order_id = cursor.lastrowid

    for pid, qty in product_counts.items():
        cursor.execute('''
            INSERT INTO order_items (order_id, product_id, quantity)
            VALUES (?, ?, ?)
        ''', (order_id, pid, qty))

        cursor.execute('''
            UPDATE inventory
            SET quantity = quantity - ?
            WHERE product_id = ?
        ''', (qty, pid))

    conn.commit()
    print(f"Order placed for customer {customer_id}.")
    return order_id


# View a customer's order history
def view_order_history(customer_id):
    """
    Displays all orders made by a customer, showing product details and quantities.
    """
    cursor.execute('''
    SELECT o.order_id, o.order_date, i.color, i.size, i.description, oi.quantity
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN inventory i ON oi.product_id = i.product_id
    WHERE o.customer_id = ?
    ORDER BY o.order_id
''', (customer_id,))


    rows = cursor.fetchall()
    if not rows:
        print("No orders found for this customer.")
        return

    print(f"Order history for customer ID {customer_id}:")
    current_order = None
    for row in rows:
        if row[0] != current_order:
            current_order = row[0]
            print(f"\nID Order {row[0]} — Date: {row[1]}")
        print(f"  - {row[5]}x {row[2]} {row[3]} — {row[4]}")

# View all customers
def view_all_customers():
    """
    Displays all customers in the database, including their passwords.
    """
    cursor.execute('SELECT customer_id, username, password FROM customers')
    customers = cursor.fetchall()

    if not customers:
        print("No customers found.")
        return

    print("👥 All Customers:")
    for customer in customers:
        print(f"ID {customer[0]} | Username: {customer[1]} | Password: {customer[2]}")

# Remove customers
def remove_customer(customer_id):
    cursor.execute("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
    if not cursor.fetchone():
        print(f" No customer with ID {customer_id}")
        return

    cursor.execute("SELECT order_id FROM orders WHERE customer_id = ?", (customer_id,))
    order_ids = [row[0] for row in cursor.fetchall()]

    for order_id in order_ids:
        cursor.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))

    cursor.execute("DELETE FROM orders WHERE customer_id = ?", (customer_id,))
    cursor.execute("DELETE FROM customers WHERE customer_id = ?", (customer_id,))

    conn.commit()
    print(f"Customer ID {customer_id} and their orders have been deleted.")

# Add more product
def restock_product(product_id, amount):
    cursor.execute("SELECT quantity FROM inventory WHERE product_id = ?", (product_id,))
    row = cursor.fetchone()
    if not row:
        print(f"Product ID {product_id} not found.")
        return

    cursor.execute('''
        UPDATE inventory
        SET quantity = quantity + ?
        WHERE product_id = ?
    ''', (amount, product_id))

    conn.commit()
    print(f"Restocked Product ID {product_id} by {amount}. New quantity: {row[0] + amount}")
