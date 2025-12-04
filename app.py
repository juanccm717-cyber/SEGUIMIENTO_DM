import os
import bcrypt
from flask import Flask, render_template, request, redirect, url_for, session, flash
from supabase import create_client

app = Flask(__name__, template_folder='templates')
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "clave_segura_temporal")
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'

# Conexión a Supabase
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Faltan SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    username = request.form['usuario']
    password = request.form['clave']
    try:
        user = supabase.table('usuarios').select('*').eq('email', username).execute()
        if user.data and len(user.data) > 0:
            db_user = user.data[0]
            if bcrypt.checkpw(password.encode('utf-8'), db_user['password_hash'].encode('utf-8')):
                session['usuario'] = db_user['email']
                session['role'] = db_user['rol']
                return redirect('/menu')
    except Exception as e:
        print(f"Error en login: {e}")
    flash('Usuario o contraseña incorrectos.', 'danger')
    return render_template('login.html')

@app.route('/menu')
def menu():
    if 'usuario' not in session:
        return redirect('/')
    return render_template('menu.html', usuario=session['usuario'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/test_conexion')
def test_conexion():
    try:
        res = supabase.table('usuarios').select('email', 'rol').execute()
        return f"<h1>Conexión OK</h1><pre>{res.data}</pre>"
    except Exception as e:
        return f"<h1>Error</h1><pre>{e}</pre>"

if __name__ == '__main__':
    app.run(debug=True)