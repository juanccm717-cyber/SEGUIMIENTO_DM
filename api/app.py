import os
import sys
import traceback
from flask import Flask, render_template, request, redirect, url_for

# === Manejo de errores para ver logs en Vercel ===
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    print("Uncaught exception:", file=sys.stderr)
    traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)

sys.excepthook = handle_exception

# === Ruta absoluta al directorio raíz del proyecto ===
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# === Inicializa Flask con la carpeta de templates correcta ===
app = Flask(__name__, template_folder=os.path.join(project_root, 'templates'))

# === Configuración de Supabase (PON TUS DATOS REALES AQUÍ) ===
SUPABASE_URL = "https://efterwiekhvmfsegmfu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVmbHRlcndpZWtodm1mc2VnbWZ1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQzNjIwMzksImV4cCI6MjA3OTkzODAzOX0.a6ZDMToIMV26z_1JErX1NXbYUmafLN-RZ37plU9TmDs"

# === Conexión a Supabase ===
from supabase import create_client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# === Rutas ===

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/menu', methods=['GET', 'POST'])
def menu():
    return render_template('menu.html', usuario="Dr. Juan")

@app.route('/registrar_paciente')
def registrar():
    return render_template('registrar_paciente.html')

@app.route('/registrar_paciente', methods=['POST'])
def guardar():
    try:
        data = {
            'nombre': request.form['nombre'],
            'dni': request.form['dni'],
            'fecha_nacimiento': request.form['fecha_nacimiento'],
            'diagnostico_dm': request.form['diagnostico_dm'] == 'si',
            'tipo_dm': request.form.get('tipo_dm') or None,
            'diagnostico_hta': request.form['diagnostico_hta'] == 'si',
            'fecha_diagnostico': request.form['fecha_diagnostico'],
            'telefono': request.form.get('telefono') or None,
            'email': request.form.get('email') or None
        }

        # Guardar en Supabase
        response = supabase.table('pacientes').insert(data).execute()

        if response.data:
            return f"""
            <h2 style="font-family: Arial, sans-serif; color: #2e7d32;">✅ Paciente registrado con éxito</h2>
            <p><strong>Nombre:</strong> {data['nombre']}<br><strong>DNI:</strong> {data['dni']}</p>
            <a href="/menu" style="display: inline-block; margin-top: 15px; padding: 8px 16px; background: #1976d2; color: white; text-decoration: none; border-radius: 4px;">← Volver al Menú</a>
            """
        else:
            return "<h2 style='color: red;'>❌ Error: No se pudo guardar en Supabase.</h2><a href='/registrar_paciente'>Reintentar</a>"

    except Exception as e:
        return f"<h3 style='color: red;'>⚠️ Error al procesar:</h3><pre>{traceback.format_exc()}</pre>"

# === Handler requerido por Vercel ===
def handler(event, context):
    with app.test_request_context(
        path=event.get('path', '/'),
        method=event.get('httpMethod', 'GET'),
        headers=event.get('headers', {})
    ):
        response = app.full_dispatch_request()
        return {
            'statusCode': response.status_code,
            'headers': dict(response.headers),
            'body': response.get_data(as_text=True)
        }