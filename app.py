from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "tu_clave_secreta_aqui"  # Cambia esto en producción

# Usuarios simulados (más adelante los conectarás a Supabase)
USUARIOS = {
    "admin": "admin123",
    "medico": "medico123",
    "enfermeria": "enfer123"
}

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def do_login():
    usuario = request.form['usuario']
    clave = request.form['clave']
    
    if usuario in USUARIOS and USUARIOS[usuario] == clave:
        session['usuario'] = usuario
        return redirect('/menu')
    else:
        return render_template('login.html', error="Usuario o contraseña incorrectos")

@app.route('/menu')
def menu():
    if 'usuario' not in session:
        return redirect('/')
    return render_template('menu.html', usuario=session['usuario'])

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect('/')