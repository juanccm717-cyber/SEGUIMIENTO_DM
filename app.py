# ==============================================================================
#               APP.PY COMPLETO PARA SEGUIMIENTO DM/HTA CON SUPABASE
# ==============================================================================
import os
import bcrypt
from flask import Flask, render_template, request, redirect, url_for, session, flash
from supabase import create_client

# --- Configuración de Flask ---
app = Flask(__name__, template_folder='templates')
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "prosecretkey_dm_hta_2025_seguro")

# --- Conexión a Supabase ---
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')  # ¡Usa service_role!

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Faltan SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Rutas ---

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def do_login():
    usuario = request.form['usuario']
    clave = request.form['clave']
    
    # Buscar usuario en Supabase
    user = supabase.table('usuarios').select('*').eq('username', usuario).execute()
    if user.data and len(user.data) > 0:
        db_user = user.data[0]
        if bcrypt.checkpw(clave.encode('utf-8'), db_user['password_hash'].encode('utf-8')):
            session['usuario'] = db_user['username']
            session['role'] = db_user['role']
            return redirect('/menu')
    
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
        # Verificar si el DNI ya existe
        existing = supabase.table('pacientes').select('dni').eq('dni', dni).execute()
        if existing.data:
            flash(f'⚠️ Paciente ya registrado con este DNI. Use el módulo de seguimiento.', 'warning')
            return render_template('registrar_paciente.html', dni=dni, nombre=nombre)
        
        # Registrar nuevo paciente
        data = {
            'dni': dni,
            'nombre': nombre,
            'fecha_nacimiento': request.form['fecha_nacimiento'],
            'diagnostico_dm': request.form['diagnostico_dm'] == 'si',
            'tipo_dm': request.form.get('tipo_dm') or None,
            'diagnostico_hta': request.form['diagnostico_hta'] == 'si',
            'fecha_diagnostico': request.form['fecha_diagnostico'],
            'telefono': request.form.get('telefono') or None,
            'email': request.form.get('email') or None
        }

        response = supabase.table('pacientes').insert(data).execute()

        if response:
            flash(f'✅ Paciente {nombre} registrado con éxito.', 'success')
            return redirect('/menu')
        else:
            flash('❌ Error al guardar en Supabase.', 'danger')

    except Exception as e:
        flash(f'⚠️ Error interno: {str(e)}', 'danger')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# --- Para desarrollo local ---
if __name__ == '__main__':
    app.run(debug=True)