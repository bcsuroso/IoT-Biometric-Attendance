import warnings
# Filter warning spesifik
warnings.filterwarnings("ignore", category=UserWarning, module='face_recognition_models')

import cv2
import face_recognition
import os
import numpy as np
import time
import paho.mqtt.client as mqtt 

# --- KONFIGURASI MQTT ---
MQTT_BROKER = "localhost" 
MQTT_PORT = 1883
MQTT_TOPIC_INPUT = "absensi/trigger"   
MQTT_TOPIC_OUTPUT = "absensi/result"   

# --- KONFIGURASI WAJAH ---
path_folder_wajah = r'C:\Users\MSI\file_anaconda\IOT\face_recognition\known_faces'
known_face_encodings = []
known_face_names = []

def load_database():
    print("--- MEMUAT DATABASE WAJAH (Tunggu sebentar...) ---")
    if not os.path.exists(path_folder_wajah):
        os.makedirs(path_folder_wajah)
        return

    for filename in os.listdir(path_folder_wajah):
        if filename.lower().endswith(('.jpg', '.png', '.jpeg')):
            image_path = os.path.join(path_folder_wajah, filename)
            image = face_recognition.load_image_file(image_path)
            try:
                # Menggunakan model default (HOG) yang CPU friendly
                encoding = face_recognition.face_encodings(image)[0]
                known_face_encodings.append(encoding)
                
                base_name = os.path.splitext(filename)[0]
                name = base_name.rsplit('_', 1)[0] if "_" in base_name else base_name
                known_face_names.append(name)
            except IndexError:
                pass
    print(f"Database Siap: {len(known_face_names)} user terdaftar.")

# --- FUNGSI UTAMA: SCANNING ---
def start_scanning(trigger_msg):
    print(f"\n[INFO] Menerima Trigger: {trigger_msg}")
    print("[INFO] Mengaktifkan Kamera...")
    
    cap = cv2.VideoCapture(0)
    qr_detector = cv2.QRCodeDetector()
    
    # Timer & Config
    start_time = time.time()
    SCAN_DURATION = 15  
    AUTH_TIMEOUT = 5    
    
    # State Logic
    pending_user = None
    auth_timer_start = 0
    is_success = False
    final_user = ""
    
    # State UI
    status_msg = "SISTEM TERKUNCI"
    header_color = (50, 50, 50) # Default Abu-abu

    while True:
        ret, frame = cap.read()
        if not ret: break
        
        current_time = time.time()
        
        # Cek Timeout Global
        if current_time - start_time > SCAN_DURATION:
            print("[TIMEOUT] Waktu habis.")
            break

        # Resize frame (0.25)
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # --- 1. DETEKSI WAJAH ---
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = [] # List untuk menyimpan nama yang akan digambar nanti

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"
            
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            if len(face_distances) > 0:
                best_match = np.argmin(face_distances)
                if matches[best_match]:
                    name = known_face_names[best_match]
                    
                    # LOGIKA: Jika wajah dikenal -> Simpan state
                    pending_user = name
                    auth_timer_start = current_time
                    start_time = current_time # Reset global timer biar gak mati
            
            face_names.append(name)

        # --- 2. LOGIKA STATE (UI Colors) ---
        status_msg = "MENCARI WAJAH..."
        header_color = (50, 50, 50) # Abu-abu
        
        if pending_user is not None:
            time_elapsed = current_time - auth_timer_start
            if time_elapsed < AUTH_TIMEOUT:
                # Mode Tunggu QR
                time_left = int(AUTH_TIMEOUT - time_elapsed)
                status_msg = f"Halo {pending_user}! Scan QR ({time_left}s)"
                header_color = (0, 165, 255) # Oranye
                
                # --- 3. DETEKSI QR ---
                data, bbox, _ = qr_detector.detectAndDecode(frame)
                if data:
                    # [VISUAL BARU] Gambar Kotak QR
                    if bbox is not None:
                        points = bbox.astype(int)
                        if points.ndim > 2: points = points[0]
                        for i in range(len(points)):
                            pt1 = tuple(points[i])
                            pt2 = tuple(points[(i+1) % len(points)])
                            cv2.line(frame, pt1, pt2, (0, 255, 255), 4) # Kuning Tebal

                    # Cek Isi QR
                    if data == pending_user:
                        print(f"[SUKSES] User: {pending_user}")
                        is_success = True
                        final_user = pending_user
                        
                        # Tampilkan visual sukses sebentar sebelum close
                        cv2.rectangle(frame, (0, 0), (frame.shape[1], 60), (0, 255, 0), -1)
                        
                        cv2.putText(frame, f"SUKSES: {final_user}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                        cv2.imshow('Sistem Absensi', frame)
                        cv2.waitKey(2000) # Tahan 2 detik biar kelihatan suksesnya
                        break 
            else:
                pending_user = None

        # --- 4. GAMBAR UI (VISUAL BARU) ---
        
        # A. Header Bar
        cv2.rectangle(frame, (0, 0), (frame.shape[1], 60), header_color, -1)
        cv2.putText(frame, status_msg, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # B. Guide Box (Kotak Tengah)
        h, w, _ = frame.shape
        cv2.rectangle(frame, (w//2 - 150, h//2 - 150), (w//2 + 150, h//2 + 150), (200, 200, 200), 1)
        
        # C. Kotak Wajah & Nama
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            top *= 4; right *= 4; bottom *= 4; left *= 4
            
            # Kotak Wajah
            cv2.rectangle(frame, (left, top), (right, bottom), header_color, 2)
            
            # Label Nama
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), header_color, cv2.FILLED)
            cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)

        cv2.imshow('Sistem Absensi', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    # --- SELESAI ---
    cap.release()
    cv2.destroyAllWindows()
    
    if is_success:
        client.publish(MQTT_TOPIC_OUTPUT, f"OPEN:{final_user}")
    else:
        client.publish(MQTT_TOPIC_OUTPUT, "TIMEOUT")

# --- MQTT CALLBACKS ---
def on_connect(client, userdata, flags, rc):
    print(f"Terhubung ke Broker. Menunggu di: {MQTT_TOPIC_INPUT}")
    client.subscribe(MQTT_TOPIC_INPUT)

def on_message(client, userdata, msg):
    start_scanning(msg.payload.decode())

# --- MAIN PROGRAM ---
if __name__ == "__main__":
    # 1. Load Database dulu
    load_database()
    
    # 2. Setup MQTT
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # --- TAMBAHAN BARU DISINI ---
        print("[INFO] Mengirim sinyal SIAP ke Node-RED...")
        client.publish("absensi/status", "SISTEM SIAP DIGUNAKAN")
        # ----------------------------

        # 3. Masuk mode standby
        print("[INFO] Menunggu trigger dari Node-RED...")
        client.loop_forever()
        
    except Exception as e:
        print(f"Gagal koneksi MQTT: {e}")