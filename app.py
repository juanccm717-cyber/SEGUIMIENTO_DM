from flask import Flask, render_template, request, redirect, url_for, session
import os

# Inicializa Flask
app = Flask(__name__, template_folder='templates')
app.secret_key = "tu_clave_secreta_aqui"

# Usuarios simulados (reemplazarás con Supabase después)
USUARIOS = {
    "admin": "admin123",
    "medico": "medico123",
    "enfermeria": "enfer123"
}

# Rutas
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

@app.route('/registrar_paciente')
def registrar():
    if 'usuario' not in session:
        return redirect('/')
    return render_template('registrar_paciente.html')

@app.route('/registrar_paciente', methods=['POST'])
def guardar_paciente():
    if 'usuario' not in session:
        return redirect('/')
    # Por ahora, solo muestra los datos
    data = {
        'nombre': request.form['nombre'],
        'dni': request.form['dni'],
        'diagnostico_dm': request.form['diagnostico_dm'],
        'diagnostico_hta': request.form['diagnostico_hta']
    }
    return f"""
    <h2>✅ Paciente {data['nombre']} registrado</h2>
    <a href="/menu">← Volver al Menú</a>
    """

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect('/')

# Solo para desarrollo local
if __name__ == '__main__':
    app.run(debug=True)