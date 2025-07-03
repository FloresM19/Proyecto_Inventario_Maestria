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
        elif method == 'PUT':
            response = requests.put(url, json=data, headers=headers, timeout=10)
        elif method == 'DELETE':
            response = requests.delete(url, timeout=10)
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
        return redirect(url_for('equipos'))
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
        return redirect(url_for('equipos'))
    else:
        flash(f'Error de login: {data.get("detail", "Usuario o contraseña incorrectos")}', 'error')
        return redirect(url_for('index'))
 
@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente', 'info')
    return redirect(url_for('index'))
 
# ========== EQUIPOS ==========
 
@app.route('/equipos')
def equipos():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    equipos_data, success = api_request('GET', '/equipos')
    if not success:
        flash(f'Error cargando equipos: {equipos_data.get("error")}', 'error')
    return render_template('equipos.html', equipos=equipos_data if success else [])
 
@app.route('/equipos/agregar', methods=['POST'])
def agregar_equipo():
    if 'user_id' not in session or session.get('tipo_usuario') != 'admin':
        flash('No tienes permisos para agregar equipos', 'error')
        return redirect(url_for('equipos'))
    data = {
        'nombre': request.form['nombre'],
        'descripcion': request.form.get('descripcion', ''),
        'estado': request.form['estado']
    }
    result, success = api_request('POST', '/equipos', data)
    if success:
        flash('Equipo agregado correctamente', 'success')
    else:
        flash(f'Error: {result.get("detail", "Error desconocido")}', 'error')
    return redirect(url_for('equipos'))
 
@app.route('/equipos/editar/<int:id>')
def editar_equipo(id):
    if 'user_id' not in session or session.get('tipo_usuario') != 'admin':
        flash('No tienes permisos para editar equipos', 'error')
        return redirect(url_for('equipos'))
    flash('Función de editar en desarrollo', 'info')
    return redirect(url_for('equipos'))
 
@app.route('/equipos/eliminar/<int:id>')
def eliminar_equipo(id):
    if 'user_id' not in session or session.get('tipo_usuario') != 'admin':
        flash('No tienes permisos para eliminar equipos', 'error')
        return redirect(url_for('equipos'))
    result, success = api_request('DELETE', f'/equipos/{id}')
    if success:
        flash('Equipo eliminado correctamente', 'success')
    else:
        flash(f'Error: {result.get("detail", "Error desconocido")}', 'error')
    return redirect(url_for('equipos'))
 
# ========== PRÉSTAMOS - NUEVO EN V3.0 ==========
 
@app.route('/prestamos')
def prestamos():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    # Obtener equipos disponibles
    equipos_data, success1 = api_request('GET', '/equipos/disponibles')
    equipos_disponibles = equipos_data if success1 else []
    # Obtener préstamos del usuario
    prestamos_data, success2 = api_request('GET', f'/prestamos/usuario/{session["user_id"]}')
    mis_prestamos = prestamos_data if success2 else []
    if not success1:
        flash(f'Error cargando equipos: {equipos_data.get("error")}', 'error')
    if not success2:
        flash(f'Error cargando préstamos: {prestamos_data.get("error")}', 'error')
    return render_template('prestamos.html',
                         equipos_disponibles=equipos_disponibles,
                         mis_prestamos=mis_prestamos)
 
@app.route('/solicitar_prestamo', methods=['POST'])
def solicitar_prestamo():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    data = {
        'equipo_id': int(request.form['equipo_id']),
        'usuario_id': session['user_id'],
        'motivo': request.form['motivo']
    }
    result, success = api_request('POST', '/prestamos', data)
    if success:
        flash('Préstamo solicitado correctamente', 'success')
    else:
        flash(f'Error: {result.get("detail", "Error desconocido")}', 'error')
    return redirect(url_for('prestamos'))
 
@app.route('/prestamos/devolver/<int:prestamo_id>')
def devolver_equipo(prestamo_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    result, success = api_request('PUT', f'/prestamos/{prestamo_id}/devolver')
    if success:
        flash('Equipo devuelto correctamente', 'success')
    else:
        flash(f'Error: {result.get("detail", "Error desconocido")}', 'error')
    return redirect(url_for('prestamos'))
 
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)