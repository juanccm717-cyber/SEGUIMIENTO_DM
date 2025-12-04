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
    
    dni = request.form['dni']
    nombre = request.form['nombre']
    
    try:
        # 🔍 Verificar si el DNI ya existe en Supabase
        existing = supabase.table('pacientes').select('dni').eq('dni', dni).execute()
        if existing.data:
            # Paciente ya existe → mostrar error
            return render_template('registrar_paciente.html', 
                                   error="⚠️ Paciente ya registrado con este DNI. Use el módulo de seguimiento.")
        
        # 🆕 Registrar nuevo paciente
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
            return f"""
            <h2 style="font-family: Arial, sans-serif; color: #2e7d32;">✅ Paciente registrado con éxito</h2>
            <p><strong>DNI:</strong> {data['dni']}<br>
               <strong>Nombre:</strong> {data['nombre']}</p>
            <a href="/menu" style="display: inline-block; margin-top: 15px; padding: 8px 16px; background: #1976d2;
               color: white; text-decoration: none; border-radius: 4px;">← Volver al Menú</a>
            """
        else:
            return render_template('registrar_paciente.html', 
                                   error="❌ Error: No se pudo guardar en Supabase.")

    except Exception as e:
        return render_template('registrar_paciente.html', 
                               error=f"⚠️ Error interno: {str(e)}")

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect('/')

# Solo para desarrollo local
if __name__ == '__main__':
    app.run(debug=True)