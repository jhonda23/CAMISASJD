from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import psycopg2, os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'secretkey123'
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# ---- CONEXIÓN A BD ----
def get_db_connection():
    return psycopg2.connect(host='db', database='selectstyle', user='postgres', password='postgres')


@app.route('/')
def index():
    return render_template('index.html')


# ---- LISTAR PRODUCTOS (JSON) ----
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
@app.route('/admin/panel')
def admin_panel():
    if session.get('user') != 'admin':
        return redirect(url_for('login', role='admin'))

    conn = get_db_connection()
    cur = conn.cursor()

    # Camisas
    cur.execute('SELECT id, name, price, image, sold_out FROM shirts;')
    shirts = cur.fetchall()

    # Paquetes mayoristas
    cur.execute('SELECT id, nombre, descripcion, precio, imagen, cantidad, agotado FROM paquetes;')
    paquetes = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('admin_panel.html', shirts=shirts, paquetes=paquetes)




@app.route('/admin/add_package', methods=['POST'])
def add_package():
    if session.get('user') != 'admin':
        return redirect(url_for('login', role='admin'))

    name = request.form['name']
    quantity = request.form['quantity']
    price = request.form['price']
    colors = request.form['colors']
    image = request.files['image']
    filename = secure_filename(image.filename)
    os.makedirs(os.path.join('static', 'uploads'), exist_ok=True)
    image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO packages (name, quantity, price, image, colors) VALUES (%s, %s, %s, %s, %s)',
                (name, quantity, price, filename, colors))
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('admin_panel'))


@app.route('/admin/delete_package/<int:package_id>')
def delete_package(package_id):
    if session.get('user') != 'admin':
        return redirect(url_for('login', role='admin'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM packages WHERE id = %s', (package_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('admin_panel'))


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


# RUTAS PARA PAQUETES MAYORISTAS

@app.route('/admin/add_paquete', methods=['POST'])
def add_paquete():
    if session.get('user') != 'admin':
        return redirect(url_for('login', role='admin'))

    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion', '')
    precio = request.form.get('precio')
    cantidad = int(request.form.get('cantidad', 12))

    imagen = request.files.get('imagen')
    filename = None
    if imagen and imagen.filename:
        filename = secure_filename(imagen.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        imagen.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO paquetes (nombre, descripcion, precio, imagen, cantidad, agotado) VALUES (%s, %s, %s, %s, %s, false)',
        (nombre, descripcion, precio, filename, cantidad)
    )
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('admin_panel'))


@app.route('/admin/delete_paquete/<int:paquete_id>', methods=['POST'])
def delete_paquete(paquete_id):
    if session.get('user') != 'admin':
        return redirect(url_for('login', role='admin'))

    conn = get_db_connection()
    cur = conn.cursor()
    # borrar imagen del disco (si existe)
    cur.execute('SELECT imagen FROM paquetes WHERE id = %s', (paquete_id,))
    row = cur.fetchone()
    if row and row[0]:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], row[0]))
        except Exception:
            pass

    cur.execute('DELETE FROM paquetes WHERE id = %s', (paquete_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('admin_panel'))


@app.route('/admin/toggle_paquete/<int:paquete_id>', methods=['POST'])
def toggle_paquete(paquete_id):
    if session.get('user') != 'admin':
        return redirect(url_for('login', role='admin'))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT agotado FROM paquetes WHERE id = %s', (paquete_id,))
    row = cur.fetchone()
    if row is None:
        cur.close()
        conn.close()
        return redirect(url_for('admin_panel'))

    nuevo_estado = not row[0]
    cur.execute('UPDATE paquetes SET agotado = %s WHERE id = %s', (nuevo_estado, paquete_id))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('admin_panel'))


# ---------- PANEL DE MAYORISTAS ----------
@app.route('/mayoristas')
def pagina_mayoristas():
    if 'mayorista' not in session:
        return redirect(url_for('login', role='wholesaler'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, nombre, descripcion, precio, imagen, cantidad, agotado FROM paquetes ORDER BY id DESC;')
    paquetes = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('pagina_mayoristas.html', paquetes=paquetes)



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
