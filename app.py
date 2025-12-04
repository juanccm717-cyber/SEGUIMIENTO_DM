from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
from supabase import create_client

# === Configuración de Flask ===
app = Flask(__name__, template_folder='templates')
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "prosecretkey_dm_hta_2025_7e3f8a9b_c4d1_4c6e_b7f2_1a2b3c4d5e6f")

# === Conexión a Supabase ===
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY')

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise RuntimeError("Faltan SUPABASE_URL o SUPABASE_ANON_KEY en las variables de entorno.")

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# === Usuarios simulados (puedes migrarlos a Supabase después) ===
USUARIOS = {
    "admin": "admin123",
    "medico": "medico123",
    "enfermeria": "enfer123"
}

# === Rutas ===

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
        flash("Usuario o contraseña incorrectos.", "error")
        return render_template('login.html')

@app.route('/menu')
def menu():
    if 'usuario' not in session:
        return redirect('/')
    return render_template('menu.html', usuario=session['usuario'])

@app.route('/admin/crear_usuario', methods=['GET', 'POST'])
def crear_usuario():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    # Solo administradores pueden crear usuarios
    if session.get('role') != 'administrador':
        flash('Acceso denegado. Solo los administradores pueden crear usuarios.', 'danger')
        return redirect(url_for('menu'))

    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()
        role = request.form.get('role')

        if not all([username, password, role]):
            flash('Todos los campos son obligatorios.', 'warning')
            return render_template('crear_usuario.html', roles=['administrador', 'medico', 'enfermeria'])

        try:
            # Verificar si el usuario ya existe
            existing = supabase.table('usuarios').select('username').eq('username', username).execute()
            if existing.data:
                flash(f'El usuario "{username}" ya existe.', 'warning')
                return render_template('crear_usuario.html', roles=['administrador', 'medico', 'enfermeria'])

            # Encriptar la contraseña
            password_bytes = password.encode('utf-8')
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

            # Insertar en Supabase
            new_user = {
                'username': username,
                'password_hash': hashed_password,
                'role': role
            }
            response = supabase.table('usuarios').insert(new_user).execute()

            if response:
                flash(f'✅ Usuario "{username}" creado con éxito.', 'success')
                return redirect(url_for('menu'))
            else:
                flash('❌ Error al guardar en Supabase.', 'danger')

        except Exception as e:
            flash(f'⚠️ Error interno: {str(e)}', 'danger')

    return render_template('crear_usuario.html', roles=['administrador', 'medico', 'enfermeria'])

@app.route('/registrar_paciente')
def registrar():
    if 'usuario' not in session:
        return redirect('/')
    return render_template('registrar_paciente.html')

@app.route('/registrar_paciente', methods=['POST'])
def guardar_paciente():
    if 'usuario' not in session:
        return redirect('/')
    
    dni = request.form['dni'].strip()
    nombre = request.form['nombre'].strip()
    
    # Verificar si el DNI ya existe
    try:
        existing = supabase.table('pacientes').select('dni').eq('dni', dni).execute()
        if existing.data:
            flash("⚠️ Paciente ya registrado con este DNI. Use el módulo de seguimiento.", "error")
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
        if response.data:
            flash(f"✅ Paciente {nombre} registrado con éxito.", "success")
            return redirect('/menu')
        else:
            flash("❌ Error al guardar en Supabase.", "error")
            return render_template('registrar_paciente.html', **request.form)

    except Exception as e:
        flash(f"⚠️ Error interno: {str(e)}", "error")
        return render_template('registrar_paciente.html', **request.form)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# === Para desarrollo local ===
if __name__ == '__main__':
    app.run(debug=True)