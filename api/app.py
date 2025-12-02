from flask import Flask, render_template, request
from supabase import create_client

# 🔑 Configura Supabase (reemplaza con tus datos)
SUPABASE_URL = "https://efterwiekhvmfsegmfu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxx"  # ← ¡Pon tu clave real aquí!
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)

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
    data = {
        'nombre': request.form['nombre'],
        'dni': request.form['dni'],
        'fecha_nacimiento': request.form['fecha_nacimiento'],
        'diagnostico_dm': request.form['diagnostico_dm'] == 'si',
        'tipo_dm': request.form.get('tipo_dm') or None,
        'diagnostico_hta': request.form['diagnostico_hta'] == 'si',
        'fecha_diagnostico': request.form['fecha_diagnostico'],
        'telefono': request.form.get('telefono') or None
    }
    supabase.table('pacientes').insert(data).execute()
    return f"<h2>✅ ¡Paciente {data['nombre']} registrado!</h2><a href='/menu'>Volver al menú</a>"

# Handler para Vercel
def handler(event, context):
    from werkzeug.test import EnvironBuilder
    from werkzeug.wrappers import Request
    with app.test_request_context(path=event['path'], method=event['httpMethod']):
        response = app.full_dispatch_request()
        return {
            'statusCode': response.status_code,
            'headers': dict(response.headers),
            'body': response.get_data(as_text=True)
        }