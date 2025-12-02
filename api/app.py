import os
import sys
import traceback
from flask import Flask, render_template, request
from dotenv import load_dotenv

# === Cargar variables de entorno (funciona en local y Vercel) ===
# En Vercel, load_dotenv() no hará nada si no hay .env, pero las vars ya están en el entorno
load_dotenv()

# === Manejo de errores para ver logs en Vercel ===
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    print("Uncaught exception:", file=sys.stderr)
    traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)

sys.excepthook = handle_exception

# === Ruta absoluta al directorio raíz ===
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# === Inicializar Flask con templates en la ubicación correcta ===
app = Flask(__name__, template_folder=os.path.join(project, 'templates'))

# === Obtener credenciales de Supabase ===
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("⚠️ ERROR: Falta SUPABASE_URL o SUPABASE_ANON_KEY en el entorno.", file=sys.stderr)
    sys.exit(1)

from supabase import create_client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# === Rutas ===

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/menu')
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

        response = supabase.table('pacientes').insert(data).execute()

        if response.
            return f"""
            <h2 style="font-family: Arial, sans-serif; color: #2e7d32;">✅ Paciente registrado con éxito</h2>
            <p><strong>Nombre:</strong> {data['nombre']}<br><strong>DNI:</strong> {data['dni']}</p>
            <a href="/menu" style="display: inline-block; margin-top: 15px; padding: 8px 16px; background: #1976d2; color: white; text-decoration: none; border-radius: 4px;">← Volver al Menú</a>
            """
        else:
            return "<h2 style='color: red;'>❌ Error: No se pudo guardar en Supabase.</h2><a href='/registrar_paciente'>Reintentar</a>"

    except Exception as e:
        return f"<h3 style='color: red;'>⚠️ Excepción:</h3><pre>{traceback.format_exc()}</pre>"

# === Handler para Vercel ===
def handler(event, context):
    with app.test_request_context(
        path=event.get('path', '/'),
        method=event.get('httpMethod', 'GET'),
        headers=event.get('headers', {})
    ):
        try:
            response = app.full_dispatch_request()
            return {
                'statusCode': response.status_code,
                'headers': dict(response.headers),
                'body': response.get_data(as_text=True)
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'body': f"Error interno:\n{traceback.format_exc()}"
            }