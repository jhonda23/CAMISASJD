from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import psycopg2, os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'secretkey123'
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def get_db_connection():
    return psycopg2.connect(host='db', database='selectstyle', user='postgres', password='postgres')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/products')
def products():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, name, price, image, sold_out FROM shirts;')
    products = [
        {'id': row[0], 'name': row[1], 'price': float(row[2]), 'image': row[3], 'sold_out': row[4]}
        for row in cur.fetchall()
    ]
    cur.close()
    conn.close()
    return jsonify(products)


# ---------- LOGIN Y REGISTRO ----------
@app.route('/login/<role>', methods=['GET', 'POST'])
def login(role):
    error = None
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']

        if role == 'admin' and user == 'admin' and pwd == 'admin123':
            session['user'] = user
            return redirect(url_for('admin_panel'))

        elif role == 'wholesaler':
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM mayoristas WHERE username=%s AND password=%s", (user, pwd))
            mayorista = cur.fetchone()
            cur.close()
            conn.close()
            if mayorista:
                session['mayorista'] = user
                return redirect(url_for('pagina_mayoristas'))
            else:
                error = "Usuario o contraseña incorrectos"

        else:
            error = "Credenciales incorrectas"

    return render_template(f'login_{role}.html', error=error)


@app.route('/register_wholesaler', methods=['GET', 'POST'])
def register_wholesaler():
    message = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO mayoristas (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        cur.close()
        conn.close()
        message = "Usuario registrado correctamente. Ahora puedes iniciar sesión."
        return redirect(url_for('login', role='wholesaler'))

    return render_template('register_wholesaler.html', message=message)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# ---------- PANEL DE ADMIN ----------
@app.route('/admin/panel', methods=['GET', 'POST'])
def admin_panel():
    if session.get('user') != 'admin':
        return redirect(url_for('login', role='admin'))

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        image = request.files['image']
        filename = secure_filename(image.filename)
        os.makedirs(os.path.join('static', 'uploads'), exist_ok=True)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        cur.execute('INSERT INTO shirts (name, price, image, sold_out) VALUES (%s, %s, %s, false)',
                    (name, price, filename))
        conn.commit()

    cur.execute('SELECT id, name, price, image, sold_out FROM shirts;')
    shirts = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin_panel.html', shirts=shirts)


@app.route('/admin/toggle/<int:shirt_id>')
def toggle_sold_out(shirt_id):
    if session.get('user') != 'admin':
        return redirect(url_for('login', role='admin'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('UPDATE shirts SET sold_out = NOT sold_out WHERE id = %s', (shirt_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('admin_panel'))


@app.route('/admin/delete/<int:shirt_id>')
def delete_shirt(shirt_id):
    if session.get('user') != 'admin':
        return redirect(url_for('login', role='admin'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM shirts WHERE id = %s', (shirt_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('admin_panel'))


# ---------- PANEL DE MAYORISTAS ----------
@app.route('/mayoristas')
def pagina_mayoristas():
    if 'mayorista' not in session:
        return redirect(url_for('login', role='wholesaler'))
    return render_template('pagina_mayoristas.html')


@app.route('/register_mayorista', methods=['GET', 'POST'])
def register_mayorista():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO mayoristas (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for('login', role='wholesaler'))

    return render_template('register_wholesaler.html')




if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
