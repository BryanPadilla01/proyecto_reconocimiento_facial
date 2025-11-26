import sqlite3
import queue
import threading
import os
import numpy as np

DB_FOLDER = os.path.join(os.getenv('APPDATA'), 'ReconocimientoFacial')
DB_PATH = os.path.join(DB_FOLDER, 'database.db')
os.makedirs(DB_FOLDER, exist_ok=True)

db_queue = queue.Queue()

def get_db_connection():
    """Establece una conexión con la base de datos SQLite."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        return conn
    except sqlite3.Error as e:
        print(f"Error al conectar con SQLite: {e}")
        return None

def init_db():
    """Crea las tablas de la base de datos (con la estructura simplificada) si no existen."""
    conn = get_db_connection()
    if not conn:
        print("CRÍTICO: No se pudo establecer conexión con la base de datos para inicializarla.")
        return
    try:
        with conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS rostros_conocidos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    encoding BLOB NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL
                )
            ''')
        print("Base de datos SQLite inicializada correctamente en:", DB_PATH)
    except sqlite3.Error as e:
        print(f"Error al inicializar las tablas de la base de datos: {e}")
    finally:
        conn.close()

def db_worker():
    """Función trabajadora que guarda solo el encoding en SQLite."""
    print("Iniciando trabajador de base de datos SQLite...")
    while True:
        try:
            data_to_save = db_queue.get()
            if data_to_save is None: break
            
            conn = get_db_connection()
            if not conn: continue

            try:
                with conn:
                    encoding_bytes = data_to_save['encoding'].tobytes()
                    conn.execute(
                        "INSERT INTO rostros_conocidos (encoding) VALUES (?)",
                        (encoding_bytes,)
                    )
                print(f"Nuevo rostro guardado en SQLite.")
            except sqlite3.Error as e:
                print(f"Error al guardar en SQLite: {e}")
            finally:
                conn.close()
            
            db_queue.task_done()
        except Exception as e:
            print(f"Error crítico en el worker de la DB: {e}")

def cargar_encodings_conocidos():
    """Carga todos los IDs y encodings desde SQLite."""
    conn = get_db_connection()
    if not conn: return []
    
    datos_rostros_conocidos = []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, encoding FROM rostros_conocidos")
        resultados = cursor.fetchall()
        for row in resultados:
            encoding_array = np.frombuffer(row[1], dtype=np.float64)
            datos_rostros_conocidos.append({"id": row[0], "encoding": encoding_array})
    except sqlite3.Error as e:
        print(f"Error al cargar encodings desde SQLite: {e}")
    finally:
        conn.close()
    print(f"Se cargaron los datos de {len(datos_rostros_conocidos)} rostros desde SQLite.")
    return datos_rostros_conocidos

def create_user(username, password_hash):
    conn = get_db_connection()
    if not conn: return False
    try:
        with conn:
            conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
        return True
    except sqlite3.IntegrityError: return False
    except sqlite3.Error as e: print(f"Error al crear usuario: {e}"); return False
    finally: conn.close()

def get_user_by_username(username):
    conn = get_db_connection()
    if not conn: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (username,))
        return cursor.fetchone()
    finally: conn.close()

def get_user_by_id(user_id):
    conn = get_db_connection()
    if not conn: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password_hash FROM users WHERE id = ?", (user_id,))
        return cursor.fetchone()
    finally: conn.close()

def get_registros_mes_actual():
    conn = get_db_connection()
    if not conn: return 0
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(id) FROM rostros_conocidos WHERE timestamp >= date('now', 'start of month')")
        return cursor.fetchone()[0]
    finally: conn.close()

def get_rostros_paginados(page=1, per_page=10):
    conn = get_db_connection()
    if not conn: return [], 0
    
    offset = (page - 1) * per_page
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(id) FROM rostros_conocidos")
        total_items = cursor.fetchone()[0]
        
        cursor.execute(
            "SELECT id, strftime('%Y-%m-%d %H:%M:%S', timestamp) FROM rostros_conocidos ORDER BY id DESC LIMIT ? OFFSET ?",
            (per_page, offset)
        )
        resultados = cursor.fetchall()
        lista_rostros = [{"id": r[0], "timestamp": r[1]} for r in resultados]
        return lista_rostros, total_items
    finally: conn.close()