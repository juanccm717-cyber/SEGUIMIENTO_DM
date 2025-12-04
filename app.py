# ==============================================================================
#               APP.PY COMPLETO PARA SEGUIMIENTO DM/HTA EN VERCEL + SUPABASE
# ==============================================================================
import os
import bcrypt
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from supabase import create_client

# --- Configuración de Flask ---
app = Flask(__name__, template_folder='templates')
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "prosecretkey_dm_hta_2025_seguro")

# --- Configuración de cookies para Vercel ---
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'

# --- Conexión a Supabase (usa SERVICE_ROLE_KEY para operaciones administrativas) ---
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')  # ¡Clave de servicio!

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Faltan SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY en Vercel")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Rutas ---

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def do_login():
    if request.method == 'GET':
        return render_template('login.html')
    
    username = request.form.get('usuario')
    password = request.form.get('clave')
    
    if not username or not password:
        flash('Usuario y contraseña son obligatorios.', 'danger')
        return render_template('login.html')
    
    # Buscar usuario en Supabase
    user = supabase.table('usuarios').select('*').eq('username', username).execute()
    if user.data and len(user.data) > 0:
        db_user = user.data[0]
        if bcrypt.checkpw(password.encode('utf-8'), db_user['password_hash'].encode('utf-8')):
            session['user_id'] = db_user['id']
            session['username'] = db_user['username']
            session['role'] = db_user['role']
            return redirect('/menu')
    
    flash('Usuario o contraseña incorrectos.', 'danger')
    return render_template('login.html')

@app.route('/menu')
def menu():
    if 'username' not in session:
        return redirect('/')
    return render_template('menu.html', usuario=session['username'])

@app.route('/registrar_paciente')
def registrar():
    if 'username' not in session:
        return redirect('/')
    return render_template('registrar_paciente.html')

@app.route('/registrar_paciente', methods=['POST'])
def guardar_paciente():
    if 'username' not in session:
        return redirect('/')
    
    dni = request.form['dni'].strip()
    nombre = request.form['nombre'].strip()
    
    if not dni or not nombre:
        flash('DNI y nombre son obligatorios.', 'warning')
        return render_template('registrar_paciente.html')
    
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
            return render_template('registrar_paciente.html')

    except Exception as e:
        flash(f'⚠️ Error interno: {str(e)}', 'danger')
        return render_template('registrar_paciente.html')

# --- GESTIÓN DE USUARIOS (solo administrador) ---
@app.route('/usuarios')
def gestionar_usuarios():
    if 'username' not in session or session.get('role') != 'administrador':
        flash('Acceso denegado.', 'danger')
        return redirect('/menu')
    
    usuarios = supabase.table('usuarios').select('*').order('username', desc=False).execute()
    return render_template('gestionar_usuarios.html', usuarios=usuarios.data)

@app.route('/admin/crear_usuario', methods=['POST'])
def crear_usuario():
    if 'username' not in session or session.get('role') != 'administrador':
        return jsonify({'success': False, 'message': 'No autorizado'}), 403

    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')

    if not all([username, password, role]):
        flash('Todos los campos son obligatorios.', 'warning')
        return redirect('/usuarios')

    # Verificar si ya existe
    existe = supabase.table('usuarios').select('id').eq('username', username).execute()
    if existe.data:
        flash(f'El usuario "{username}" ya existe.', 'warning')
        return redirect('/usuarios')

    # Encriptar contraseña
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Insertar en Supabase
    nuevo = {
        'username': username,
        'password_hash': hashed,
        'role': role
    }
    supabase.table('usuarios').insert(nuevo).execute()
    flash(f'Usuario "{username}" creado con éxito.', 'success')
    return redirect('/usuarios')

@app.route('/admin/eliminar_usuario/<usuario_id>', methods=['POST'])
def eliminar_usuario(usuario_id):
    if 'username' not in session or session.get('role') != 'administrador':
        flash('No autorizado.', 'danger')
        return redirect('/usuarios')

    if usuario_id == session.get('user_id'):
        flash('No puedes eliminarte a ti mismo.', 'danger')
        return redirect('/usuarios')

    supabase.table('usuarios').delete().eq('id', usuario_id).execute()
    flash('Usuario eliminado con éxito.', 'success')
    return redirect('/usuarios')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# --- Para desarrollo local ---
if __name__ == '__main__':
    app.run(debug=True)