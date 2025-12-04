import os
import bcrypt
from flask import Flask, render_template, request, redirect, url_for, session, flash
from supabase import create_client

# --- Configuración de Flask ---
app = Flask(__name__, template_folder='templates')
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "clave_segura_temporal")

# --- Conexión a Supabase (usa SERVICE_ROLE_KEY) ---
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')  # ¡Clave de servicio!

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Faltan SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Rutas ---

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def do_login():
    username = request.form['usuario']
    password = request.form['clave']
    
    try:
        # Buscar usuario en Supabase
        user = supabase.table('usuarios').select('*').eq('username', username).execute()
        if user.data and len(user.data) > 0:
            db_user = user.data[0]
            if bcrypt.checkpw(password.encode('utf-8'), db_user['password_hash'].encode('utf-8')):
                session['usuario'] = db_user['username']
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

@app.route('/registrar_paciente')
def registrar():
    if 'usuario' not in session:
        return redirect('/')
    return render_template('registrar_paciente.html')

@app.route('/registrar_paciente', methods=['POST'])
def guardar_paciente():
    if 'usuario' not in session:
        return redirect('/')
    
    dni = request.form['dni']
    nombre = request.form['nombre']
    
    try:
        existing = supabase.table('pacientes').select('dni').eq('dni', dni).execute()
        if existing.data:
            flash('⚠️ Paciente ya registrado con este DNI.', 'warning')
            return render_template('registrar_paciente.html', dni=dni, nombre=nombre)
        
        data = {
            'dni': dni,
            'nombres_apellidos': nombre,
            'diabetes_mellitus': request.form['diagnostico_dm'] == 'si',
            'hipertension_arterial': request.form['diagnostico_hta'] == 'si',
            'fecha_nacimiento': request.form['fecha_nacimiento'],
            'fecha_diagnostico': request.form['fecha_diagnostico'],
            'telefono': request.form.get('telefono'),
            'tipo_financiamiento': request.form.get('tipo_financiamiento', 'SIS')
        }
        supabase.table('pacientes').insert(data).execute()
        flash(f'✅ Paciente {nombre} registrado con éxito.', 'success')
        return redirect('/menu')
    
    except Exception as e:
        flash(f'⚠️ Error: {str(e)}', 'danger')
        return render_template('registrar_paciente.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)