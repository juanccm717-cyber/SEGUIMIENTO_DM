from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'clave_secreta_para_sesiones'  # Cambia esto por una clave segura

# Usuarios simulados para probar el login
usuarios = {
    'admin': '1234',
    'doctor': 'abcd'
}

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in usuarios and usuarios[username] == password:
            session['usuario'] = username
            return redirect(url_for('menu'))
        else:
            error = 'Usuario o contraseña inválidos'
    return render_template('login.html', error=error)

@app.route('/menu')
def menu():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    usuario = session['usuario']
    return render_template('menu.html', usuario=usuario)

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)