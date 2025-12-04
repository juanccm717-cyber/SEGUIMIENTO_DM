import os
import bcrypt
from flask import Flask, render_template, request, redirect, url_for, session, flash
from supabase import create_client

# --- Configuración de Flask ---
app = Flask(__name__, template_folder='templates')
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "clave_segura_dm_hta_2025")

# --- Conexión a Supabase (usa SERVICE_ROLE_KEY) ---
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')  # ¡Clave de servicio!

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Faltan SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Rutas ---

@app.route('/')
def home():
    """Redirige a la página de login."""
    return redirect(url_for('login_page'))

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    """Maneja la página de login (GET) y el procesamiento del formulario (POST)."""
    if request.method == 'GET':
        return render_template('login.html')
    
    # --- Recoger datos del formulario ---
    username = request.form.get('username')
    password = request.form.get('password')
    fingerprint = request.form.get('fingerprint')
    user_agent = request.headers.get('User-Agent')
    
    if not all([username, password, fingerprint]):
        flash('Faltan datos para el inicio de sesión. Asegúrate de que JavaScript esté habilitado.', 'warning')
        return redirect(url_for('login_page'))
    
    try:
        # Buscar usuario en Supabase
        user = supabase.table('usuarios').select('*').eq('username', username).execute()
        if user.data and len(user.data) > 0:
            db_user = user.data[0]
            if bcrypt.checkpw(password.encode('utf-8'), db_user['password_hash'].encode('utf-8')):
                user_role_cleaned = db_user['role'].strip().lower()
                
                if user_role_cleaned == 'administrador':
                    session['user_id'] = db_user['id']
                    session['username'] = db_user['username']
                    session['role'] = db_user['role']
                    return redirect(url_for('menu'))
                else:
                    # Verificar dispositivo autorizado
                    device = supabase.table('dispositivos_autorizados').select('id').eq('usuario_id', db_user['id']).eq('huella_dispositivo', fingerprint).execute()
                    if device.data:
                        session['user_id'] = db_user['id']
                        session['username'] = db_user['username']
                        session['role'] = db_user['role']
                        return redirect(url_for('menu'))
                    else:
                        # Crear solicitud de acceso
                        existing_request = supabase.table('solicitudes_acceso').select('id').eq('usuario_id', db_user['id']).eq('huella_dispositivo', fingerprint).eq('estado', 'pendiente').execute()
                        if not existing_request.data:
                            supabase.table('solicitudes_acceso').insert({
                                'usuario_id': db_user['id'],
                                'huella_dispositivo': fingerprint,
                                'user_agent_info': user_agent
                            }).execute()
                        flash('Dispositivo no reconocido. Se ha enviado una solicitud de acceso al administrador.', 'info')
                        return redirect(url_for('login_page'))
        
        flash('Nombre de usuario o contraseña incorrectos.', 'danger')
        return redirect(url_for('login_page'))
    
    except Exception as e:
        print(f"Error en login: {e}")
        flash('Ocurrió un error en el servidor. Contacte al soporte.', 'danger')
        return redirect(url_for('login_page'))

@app.route('/menu')
def menu():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    return render_template('menu.html', usuario=session['username'])

@app.route('/registrar_paciente', methods=['GET', 'POST'])
def registrar_paciente():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    
    if request.method == 'POST':
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
                'fecha_nacimiento': request.form['fecha_nacimiento'],
                'diagnostico_dm': request.form['diagnostico_dm'] == 'si',
                'tipo_dm': request.form.get('tipo_dm') or None,
                'diagnostico_hta': request.form['diagnostico_hta'] == 'si',
                'fecha_diagnostico': request.form['fecha_diagnostico'],
                'telefono': request.form.get('telefono') or None,
                'email': request.form.get('email') or None
            }
            supabase.table('pacientes').insert(data).execute()
            flash(f'✅ Paciente {nombre} registrado con éxito.', 'success')
            return redirect(url_for('menu'))
        
        except Exception as e:
            print(f"Error al registrar paciente: {e}")
            flash('❌ Error al guardar en Supabase.', 'danger')
    
    return render_template('registrar_paciente.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    app.run(debug=True)