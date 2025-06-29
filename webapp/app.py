from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests
import os

app = Flask(__name__)
app.secret_key = 'Proyecto_Maestria_2025'

API_URL = os.getenv('API_URL', 'http://api:8000')

# Función helper para peticiones a la API
def api_request(method, endpoint, data=None):
    try:
        url = f'{API_URL}{endpoint}'
        headers = {'Content-Type': 'application/json'}
        
        if method == 'GET':
            response = requests.get(url, timeout=10)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=10)
        
        if response.status_code in [200, 201]:
            return response.json(), True
        else:
            error_data = response.json() if response.text else {"error": "Error desconocido"}
            return error_data, False
            
    except requests.exceptions.ConnectionError:
        return {"error": "No se puede conectar con la API"}, False
    except requests.exceptions.Timeout:
        return {"error": "Timeout en la conexión con la API"}, False
    except Exception as e:
        return {"error": str(e)}, False

# ========== AUTENTICACIÓN ==========

@app.route('/')
def index():
    if 'user_id' in session:
        return render_template('welcome.html')
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    data, success = api_request('POST', '/login', {'username': username, 'password': password})
    
    if success:
        user = data['user']
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['tipo_usuario'] = user['tipo_usuario']
        session['nombre_completo'] = user['nombre_completo']
        flash(f'¡Bienvenido {user["nombre_completo"]}!', 'success')
        return redirect(url_for('index'))
    else:
        flash(f'Error de login: {data.get("detail", "Usuario o contraseña incorrectos")}', 'error')
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
