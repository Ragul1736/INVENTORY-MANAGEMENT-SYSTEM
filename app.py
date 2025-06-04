import sqlite3
from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime

app = Flask(__name__)

def init_db():
    with sqlite3.connect('inventory.db') as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            stock INTEGER NOT NULL,
            price REAL NOT NULL
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            quantity INTEGER NOT NULL,
            order_date TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )''')
        conn.commit()

@app.route('/')
def index():
    with sqlite3.connect('inventory.db') as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        # Total products
        c.execute('SELECT COUNT(*) AS total_products FROM products')
        total_products = c.fetchone()['total_products']
        # Total suppliers
        c.execute('SELECT COUNT(*) AS total_suppliers FROM suppliers')
        total_suppliers = c.fetchone()['total_suppliers']
        # Total orders
        c.execute('SELECT COUNT(*) AS total_orders FROM orders')
        total_orders = c.fetchone()['total_orders']
        # Low stock products (stock < 10)
        c.execute('SELECT id, name, stock FROM products WHERE stock < 10')
        low_stock_products = c.fetchall()
        # Recent orders (last 5)
        c.execute('SELECT orders.id, products.name, orders.quantity, orders.order_date, orders.status '
                  'FROM orders JOIN products ON orders.product_id = products.id '
                  'ORDER BY orders.order_date DESC LIMIT 5')
        recent_orders = c.fetchall()
    return render_template('index.html', 
                         total_products=total_products,
                         total_suppliers=total_suppliers,
                         total_orders=total_orders,
                         low_stock_products=low_stock_products,
                         recent_orders=recent_orders)

@app.route('/products')
def products():
    with sqlite3.connect('inventory.db') as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM products')
        products = c.fetchall()
    return render_template('products.html', products=products)

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        stock = int(request.form['stock'])
        price = float(request.form['price'])
        with sqlite3.connect('inventory.db') as conn:
            c = conn.cursor()
            c.execute('INSERT INTO products (name, description, stock, price) VALUES (?, ?, ?, ?)',
                      (name, description, stock, price))
            conn.commit()
        return redirect(url_for('products'))
    return render_template('add_product.html')

@app.route('/edit_product/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    with sqlite3.connect('inventory.db') as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        if request.method == 'POST':
            name = request.form['name']
            description = request.form['description']
            stock = int(request.form['stock'])
            price = float(request.form['price'])
            c.execute('UPDATE products SET name=?, description=?, stock=?, price=? WHERE id=?',
                      (name, description, stock, price, id))
            conn.commit()
            return redirect(url_for('products'))
        c.execute('SELECT * FROM products WHERE id=?', (id,))
        product = c.fetchone()
    return render_template('edit_product.html', product=product)

@app.route('/delete_product/<int:id>')
def delete_product(id):
    with sqlite3.connect('inventory.db') as conn:
        c = conn.cursor()
        c.execute('DELETE FROM products WHERE id=?', (id,))
        conn.commit()
    return redirect(url_for('products'))

@app.route('/suppliers')
def suppliers():
    with sqlite3.connect('inventory.db') as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM suppliers')
        suppliers = c.fetchall()
    return render_template('suppliers.html', suppliers=suppliers)

@app.route('/add_supplier', methods=['GET', 'POST'])
def add_supplier():
    if request.method == 'POST':
        name = request.form['name']
        contact = request.form['contact']
        with sqlite3.connect('inventory.db') as conn:
            c = conn.cursor()
            c.execute('INSERT INTO suppliers (name, contact) VALUES (?, ?)', (name, contact))
            conn.commit()
        return redirect(url_for('suppliers'))
    return render_template('add_supplier.html')

@app.route('/orders')
def orders():
    with sqlite3.connect('inventory.db') as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT orders.*, products.name FROM orders JOIN products ON orders.product_id = products.id')
        orders = c.fetchall()
        c.execute('SELECT id, name FROM products')
        products = c.fetchall()
    return render_template('orders.html', orders=orders, products=products)

@app.route('/place_order', methods=['POST'])
def place_order():
    product_id = int(request.form['product_id'])
    quantity = int(request.form['quantity'])
    with sqlite3.connect('inventory.db') as conn:
        c = conn.cursor()
        c.execute('SELECT stock FROM products WHERE id=?', (product_id,))
        stock = c.fetchone()[0]
        if stock >= quantity:
            c.execute('UPDATE products SET stock = stock - ? WHERE id=?', (quantity, product_id))
            c.execute('INSERT INTO orders (product_id, quantity, order_date, status) VALUES (?, ?, ?, ?)',
                      (product_id, quantity, datetime.now().strftime('%Y-%m-%d'), 'Placed'))
            conn.commit()
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Insufficient stock'})

@app.route('/reports')
def reports():
    with sqlite3.connect('inventory.db') as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM products')
        products = c.fetchall()
        c.execute('SELECT orders.*, products.name, products.price FROM orders JOIN products ON orders.product_id = products.id')
        orders = c.fetchall()
    return render_template('reports.html', products=products, orders=orders)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)