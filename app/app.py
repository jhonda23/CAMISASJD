from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import psycopg2, os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'secretkey123'
UPLOAD_FOLDER = 'static/uploads'  # ruta relativa dentro de flask
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

@app.route('/login/<role>', methods=['GET', 'POST'])
def login(role):
    error = None
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']
        if role == 'admin' and user == 'admin' and pwd == 'admin123':
            session['user'] = user
            return redirect(url_for('admin_panel'))
        elif role == 'wholesaler' and user == 'mayorista' and pwd == 'mayor123':
            session['user'] = user
            return f"<h1>Bienvenido, {user.title()} ({role.title()})</h1>"
        else:
            error = "Credenciales incorrectas"
    return render_template('login.html', role=role.title(), error=error)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

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



from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2

@app.route('/login_mayorista', methods=['GET', 'POST'])
def login_mayorista():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = psycopg2.connect(
            host="db",
            database="selectstyle",
            user="postgres",
            password="postgres"
        )
        cur = conn.cursor()
        cur.execute("SELECT * FROM mayoristas WHERE username=%s AND password=%s", (username, password))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            session['mayorista'] = username
            return redirect(url_for('pagina_mayoristas'))
        else:
            return "Usuario o contraseña incorrectos"

    return render_template('login_mayorista.html')


@app.route('/mayoristas')
def pagina_mayoristas():
    if 'mayorista' not in session:
        return redirect(url_for('login_mayorista'))
    return "<h1>Bienvenido Mayorista</h1>"





if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
