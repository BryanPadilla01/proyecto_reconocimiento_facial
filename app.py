from flask import Flask, render_template, Response, request, redirect, url_for, flash, send_file
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import cv2
import threading
import math
import os
import webbrowser
from threading import Timer
import pandas as pd
import io
from datetime import datetime

from face_processor import procesar_frame
from db_manager import (init_db, db_worker, get_rostros_paginados, get_registros_mes_actual, 
                        create_user, get_user_by_id, get_user_by_username, get_all_registros_raw,
                        get_stats_por_dia_semana, get_stats_tendencia)

app = Flask(__name__)
app.secret_key = 'clave-secreta' 

init_db()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Por favor, inicie sesión para acceder a esta página."
login_manager.login_message_category = "warning"

class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

@login_manager.user_loader
def load_user(user_id):
    user_data = get_user_by_id(user_id)
    if user_data:
        return User(id=user_data[0], username=user_data[1], password_hash=user_data[2])
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_data = get_user_by_username(username)
        if user_data and check_password_hash(user_data[2], password):
            user = User(id=user_data[0], username=user_data[1], password_hash=user_data[2])
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos. Por favor, intente de nuevo.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Ha cerrado la sesión exitosamente.', 'success')
    return redirect(url_for('login'))

video_capture = cv2.VideoCapture(0)
db_thread = threading.Thread(target=db_worker, daemon=True)
db_thread.start()

def generar_frames():
    while True:
        success, frame = video_capture.read()
        if not success: break
        else:
            frame_procesado = procesar_frame(frame)
            ret, buffer = cv2.imencode('.jpg', frame_procesado)
            if not ret: continue
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
@login_required
def dashboard():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    rostros, total_items = get_rostros_paginados(page, per_page)
    total_pages = math.ceil(total_items / per_page) if total_items > 0 else 0
    registros_mes = get_registros_mes_actual()
    return render_template('dashboard.html', 
                           rostros=rostros, 
                           registros_mes=registros_mes,
                           page=page, 
                           total_pages=total_pages,
                           total_items=total_items)

@app.route('/api/dashboard_data')
@login_required
def dashboard_data():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    rostros, total_items = get_rostros_paginados(page, per_page)
    total_pages = math.ceil(total_items / per_page) if total_items > 0 else 0
    registros_mes = get_registros_mes_actual()
    return {
        "rostros": rostros,
        "registros_mes": registros_mes,
        "total_items": total_items,
        "page": page,
        "total_pages": total_pages
    }

@app.route('/export/excel')
@login_required
def export_excel():
    data = get_all_registros_raw()
    if not data:
        flash('No hay datos para exportar.', 'warning')
        return redirect(url_for('dashboard'))
    
    df = pd.DataFrame(data)
    
    #Genera un archivo en memoria (Buffer)
    output = io.BytesIO()
    #Usa ExcelWriter para guardar en el buffer
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Reporte_Visitas')
    
    output.seek(0)
    
    filename = f"Reporte_Museo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(output, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/export/csv')
@login_required
def export_csv():
    data = get_all_registros_raw()
    if not data:
        flash('No hay datos para exportar.', 'warning')
        return redirect(url_for('dashboard'))
        
    df = pd.DataFrame(data)
    
    #Genera un CSV en memoria
    output = io.StringIO()
    df.to_csv(output, index=False, sep=';', encoding='utf-8-sig') # sep=';' es mejor para Excel en español
    
    #Convierte a bytes para send_file
    mem = io.BytesIO()
    mem.write(output.getvalue().encode('utf-8-sig'))
    mem.seek(0)
    
    filename = f"Reporte_Museo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return send_file(mem, as_attachment=True, download_name=filename, mimetype='text/csv')

@app.route('/api/charts_data')
@login_required
def charts_data():
    #Datos para Gráfico Semanal
    raw_semana = get_stats_por_dia_semana()
    #Mapear 0-6 a Nombres de días. Inicializamos todo en 0.
    dias_map = {0: 'Domingo', 1: 'Lunes', 2: 'Martes', 3: 'Miércoles', 4: 'Jueves', 5: 'Viernes', 6: 'Sábado'}
    conteo_semana = {k: 0 for k in dias_map.keys()}
    
    for dia_num, count in raw_semana:
        conteo_semana[int(dia_num)] = count
        
    #Datos para Tendencia
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    raw_tendencia = get_stats_tendencia(start_date, end_date)
    fechas = [row[0] for row in raw_tendencia]
    valores = [row[1] for row in raw_tendencia]
    
    return {
        "semana_labels": [dias_map[i] for i in range(7)], # Ordenado Dom a Sab
        "semana_data": [conteo_semana[i] for i in range(7)],
        "tendencia_labels": fechas,
        "tendencia_data": valores
    }

@app.route('/video_feed')
@login_required
def video_feed():
    return Response(generar_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == '__main__':
    Timer(2, open_browser).start()
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)