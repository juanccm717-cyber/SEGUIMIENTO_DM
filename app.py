# ==============================================================================
#               APP.PY COMPLETO PARA SEGUIMIENTO DM/HTA CON SUPABASE
# ==============================================================================
import os
import bcrypt
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from supabase import create_client

# --- Configuración de Flask ---
app = Flask(__name__, template_folder='templates')
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "prosecretkey_dm_hta_2025_seguro")

# --- Conexión a Supabase (usa SERVICE_ROLE_KEY para operaciones críticas) ---
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')  # ¡Usa la clave de servicio!

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Faltan SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Rutas ---
@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def do_login():
    username = request.form['username']
    password = request.form['password']
    
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
    return redirect('/')

@app.route('/menu')
def menu():
    if 'username' not in session:
        return redirect('/')
    return render_template('menu.html', usuario=session['username'])

# --- RUTA DE GESTIÓN DE USUARIOS (nueva) ---
@app.route('/usuarios')
def gestionar_usuarios():
    if 'username' not in session or session.get('role') != 'administrador':
        flash('Acceso denegado.', 'danger')
        return redirect('/menu')
    
    # Obtener todos los usuarios
    usuarios = supabase.table('usuarios').select('*').order('username', desc=False).execute()
    return render_template('gestionar_usuarios.html', usuarios=usuarios.data)

@app.route('/admin/crear_usuario', methods=['POST'])
def crear_usuario():
    if 'username' not in session or session.get('role') != 'administrador':
        return jsonify({'success': False, 'message': 'No autorizado'}), 403

    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')
    nombre_completo = request.form.get('nombre_completo')
    dni = request.form.get('dni')

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
        'role': role,
        'nombre_completo': nombre_completo,
        'dni': dni
    }
    supabase.table('usuarios').insert(nuevo).execute()
    flash(f'Usuario "{username}" creado con éxito.', 'success')
    return redirect('/usuarios')

@app.route('/admin/eliminar_usuario/<usuario_id>', methods=['POST'])
def eliminar_usuario(usuario_id):
    if 'username' not in session or session.get('role') != 'administrador':
        return jsonify({'success': False, 'message': 'No autorizado'}), 403

    # Evitar autoeliminación
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

# --- Otras rutas (registrar_paciente, etc.) las agregaremos después ---
if __name__ == '__main__':
    app.run(debug=True)