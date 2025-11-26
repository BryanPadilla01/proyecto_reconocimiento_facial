# face_processor.py
import cv2
import face_recognition
import numpy as np
import time
import os
from db_manager import cargar_encodings_conocidos, db_queue

TOLERANCIA = 0.6
datos_rostros_conocidos_db = cargar_encodings_conocidos()
trackers = []
tracker_statuses = []
tracker_ids = []
frame_counter = 0
FRAMES_A_REINICIAR_BUSQUEDA = 10
FRAMES_PARA_SINCRONIZAR_DB = 100

texto_estado_global = "A) No Hay Persona detectada"
color_texto_global = (0, 0, 255)

try:
    cascade_path = os.path.join(cv2.data.haarcascades, 'haarcascade_frontalface_default.xml')
    face_cascade = cv2.CascadeClassifier(cascade_path)
    if face_cascade.empty(): raise IOError("No se pudo cargar Haar cascade")
    print("Clasificador Haar Cascade cargado exitosamente.")
except Exception as e:
    print(f"Error crítico al cargar Haar Cascade: {e}"); exit()


def procesar_frame(frame):
    global frame_counter, texto_estado_global, color_texto_global
    global trackers, tracker_statuses, tracker_ids, datos_rostros_conocidos_db

    if frame_counter > 0 and frame_counter % FRAMES_PARA_SINCRONIZAR_DB == 0:
        datos_rostros_conocidos_db = cargar_encodings_conocidos()
        print("--- Memoria de rostros sincronizada con la base de datos ---")

    if frame_counter % FRAMES_A_REINICIAR_BUSQUEDA == 0:
        trackers.clear(); tracker_statuses.clear(); tracker_ids.clear()
        
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Calibración agresiva para evitar falsos positivos
        detections_haar = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=6, minSize=(90, 90))
        
        if len(detections_haar) == 0:
            texto_estado_global = "A) No Hay Persona detectada"
            color_texto_global = (0, 0, 255)
        else:
            ubicaciones_rostros = [(y, x + w, y + h, x) for (x, y, w, h) in detections_haar]
            encodings_rostros_actuales = face_recognition.face_encodings(frame, ubicaciones_rostros)
            
            encodings_solo_db = [rostro['encoding'] for rostro in datos_rostros_conocidos_db]

            for i, current_encoding in enumerate(encodings_rostros_actuales):
                (x, y, w, h) = detections_haar[i]
                match_id = None
                if encodings_solo_db:
                    distancias_db = face_recognition.face_distance(encodings_solo_db, current_encoding)
                    best_db_match_index = np.argmin(distancias_db)
                    if distancias_db[best_db_match_index] < TOLERANCIA:
                        match_id = datos_rostros_conocidos_db[best_db_match_index]['id']
                
                tracker = cv2.TrackerCSRT_create()
                tracker.init(frame, (x, y, w, h))
                trackers.append(tracker)
                tracker_ids.append(match_id)
                
                if match_id is not None:
                    tracker_statuses.append("C")
                else:
                    tracker_statuses.append("B")
                    db_queue.put({'encoding': current_encoding})
                    datos_rostros_conocidos_db.append({"id": "Nuevo", "encoding": current_encoding})
    else:
        if not trackers:
            texto_estado_global = "A) No Hay Persona detectada"
            color_texto_global = (0, 0, 255)
        else:
            for i in range(len(trackers)):
                success, bbox = trackers[i].update(frame)
                if success:
                    (x, y, w, h) = [int(v) for v in bbox]
                    status_code, face_id = tracker_statuses[i], tracker_ids[i]
                    color = (0, 255, 0) if status_code == "B" else (255, 165, 0)
                    texto_estado_global = f"B) Persona Detectada" if status_code == "B" else f"C) Persona Ya Detectada (ID: {face_id})"
                    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                    color_texto_global = color
                else:
                    pass

    frame_counter += 1
    font_face = cv2.FONT_HERSHEY_DUPLEX
    cv2.putText(frame, texto_estado_global, (10, 30), font_face, 0.7, color_texto_global, 2)
    return frame