from flask import Flask, render_template, request, redirect, url_for, session, flash
from supabase import create_client
import os, bcrypt

app = Flask(__name__, template_folder='templates')
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "clave_segura_temporal")
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
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
        res = supabase.table('usuarios').select('email', 'rol', 'password_hash').execute()
        html = ['<!DOCTYPE html><html><body><h1>Usuarios en Supabase</h1><table border=1>']
        html.append('<tr><th>email</th><th>rol</th><th>hash (primeros 20 carácteres)</th></tr>')
        for u in res.data:
            html.append(f'<tr><td>{u["email"]}</td><td>{u["rol"]}</td><td>{u["password_hash"][:20]}...</td></tr>')
        html.append('</table></body></html>')
        return ''.join(html)
    except Exception as e:
        return f'<!DOCTYPE html><html><body><h1>Error</h1><pre>{e}</pre></body></html>'


def handler(environ, start_response):
    return app(environ, start_response)