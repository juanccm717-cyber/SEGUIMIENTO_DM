from flask import Flask, render_template, request
import os

# App principal (DEBE llamarse 'app')
app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))

@app.route('/')
def home():
    return "<h1>✅ App Flask funcionando en Vercel</h1>"

@app.route('/test')
def test():
    return "Funciona sin errores."

# Esta variable es obligatoria
# Vercel busca una variable global llamada 'app' que sea WSGI
# Flask ya es WSGI-compatible por defecto