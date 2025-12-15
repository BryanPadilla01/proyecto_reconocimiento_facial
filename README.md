# Sistema de Conteo de Visitantes

Aplicación web basada en **Flask** y **OpenCV** para detectar y contar visitantes únicos mediante reconocimiento facial, evitando duplicados en las estadísticas.

## Requisitos Previos

Para que la librería de reconocimiento facial funcione en **Windows con Python 3.11**, es obligatorio tener instalado lo siguiente antes de empezar:

1.  **Python 3.11.9** (Asegúrate de marcar "Add to PATH" al instalar).
2.  **Git** instalado.
3.  **Dlib**:
    *   Descárgalo desde el [repositorio de Github](https://github.com/z-mahmud22/Dlib_Windows_Python3.x).
    *   Descargar el archivo **dlib-19.24.1-cp311-cp311-win_amd64.whl**.
    *   Mover el archivo a la carpeta de la aplicación.

---

## Instalación Paso a Paso

### 1. Clonar el repositorio
Abre tu terminal y ejecuta:
```bash
git clone https://github.com/TU_USUARIO/TU_REPOSITORIO.git
cd TU_REPOSITORIO
```

### 2. Crear entorno virtual
```bash
python -m venv venv
```
*   **Activar en Windows:** `venv\Scripts\activate`

### 3. Instalar librerías

---

## Archivo `requirements.txt`
Crea un archivo llamado `requirements.txt` en la carpeta de tu proyecto y pega esto:

```text
blinker==1.9.0
click==8.3.1
colorama==0.4.6
face-recognition==1.3.0
face_recognition_models==0.3.0
Flask==2.3.3
Flask-Login==0.6.3
itsdangerous==2.2.0
Jinja2==3.1.6
MarkupSafe==3.0.3
numpy==1.24.4
opencv-contrib-python==4.8.1.78
pillow==12.0.0
psycopg2-binary==2.9.9
Werkzeug==3.1.3
```
Ejecuta el comando:
```bash
pip install -r requirements.txt
```

---

## Dlib
Ejecuta el comando:
```bash
python -m pip install dlib-19.24.1-cp311-cp311-win_amd64.whl
```

---

## Ejecutar el Proyecto

1.  Con el entorno activado, ejecuta:
    ```bash
    python app.py
    ```
2.  El sistema abrirá automáticamente el navegador. Si no, ve a:
    `http://127.0.0.1:5000`

### Credenciales Iniciales
*   Ve a la pestaña **Registro** (`/register`) para crear tu primer usuario administrador.
*   Luego inicia sesión para ver el Dashboard y la cámara.
