import os

os.environ["TF_USE_LEGACY_KERAS"] = "1"
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 

import tensorflow as tf
tf.get_logger().setLevel('ERROR')

import cv2
from mtcnn.mtcnn import MTCNN
from deepface import DeepFace
import requests
import time
import logging
from collections import deque

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='camera.log', filemode='a')
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(console_handler)

DB_PATH = "datasets/"
MODEL_NAME = "VGG-Face"
API_URL = "http://127.0.0.1:5000"
FRAME_PROCESS_RATE = 5
BOX_PERSISTENCE = 60

HISTORY_LENGTH = 10      
PASSING_THRESHOLD = 7    

def main():
    detector = MTCNN()
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) 

    if not cap.isOpened():
        logging.error("Error: Could not open webcam.")
        return

    frame_count = 0
    active_drawings = []
    
    liveness_history = {} 

    logging.info("Camera script started. Liveness + Attendance ACTIVE.")
    print("System Ready. Liveness Detection is ENABLED.")

    while True:
        ret, frame = cap.read()
        if not ret: break

        if frame_count % FRAME_PROCESS_RATE == 0:
            try:
                detected_faces = detector.detect_faces(frame)
                
                if detected_faces:
                    new_drawings = []
                    
                    for face in detected_faces:
                        if face['confidence'] < 0.9: continue

                        x, y, w, h = face['box']
                        pad_x, pad_y = int(w * 0.1), int(h * 0.1)
                        x1, y1 = max(0, x - pad_x), max(0, y - pad_y)
                        x2, y2 = min(frame.shape[1], x + w + pad_x), min(frame.shape[0], y + h + pad_y)
                        
                        cropped_face = frame[y1:y2, x1:x2]
                        if cropped_face.size == 0: continue

                        user_id = None
                        try:
                            dfs = DeepFace.find(img_path=cropped_face,
                                                db_path=DB_PATH,
                                                model_name=MODEL_NAME,
                                                enforce_detection=False,
                                                silent=True)
                            if dfs and not dfs[0].empty:
                                identity_path = dfs[0]['identity'].iloc[0]
                                user_id = os.path.basename(os.path.dirname(identity_path))
                        except: pass

                        if not user_id: continue 

                        is_real_frame = False
                        try:
                            spoof_obj = DeepFace.extract_faces(
                                img_path=cropped_face, 
                                anti_spoofing=True, 
                                enforce_detection=False,
                                detector_backend='skip'
                            )
                            if spoof_obj:
                                is_real_frame = spoof_obj[0]['is_real']
                        except Exception:
                            is_real_frame = False 

                        if user_id not in liveness_history:
                            liveness_history[user_id] = deque(maxlen=HISTORY_LENGTH)
                        
                        liveness_history[user_id].append(is_real_frame)
                        
                        real_votes = liveness_history[user_id].count(True)
                        is_verified_real = real_votes >= PASSING_THRESHOLD

                        if is_verified_real:
                            new_drawings.append({
                                'box': (x, y, w, h), 'color': (0, 255, 0),
                                'text': f"{user_id} (REAL)", 'timer': BOX_PERSISTENCE
                            })
                            
                            try:
                                if user_id.startswith('student_'):
                                    logging.info(f"Student {user_id} verified real. Logging...")
                                    res = requests.post(f"{API_URL}/log_student_entry_auto", json={"user_id": user_id})
                                    logging.info(f"API: {res.json().get('message', 'OK')}")
                                elif user_id.startswith('faculty_'):
                                    logging.info(f"Faculty {user_id} verified real. Starting class...")
                                    res = requests.post(f"{API_URL}/start_class", json={"faculty_id": user_id})
                                    logging.info(f"API: {res.json().get('message', 'OK')}")
                            except Exception as e:
                                logging.error(f"API Error: {e}")
                        else:
                            new_drawings.append({
                                'box': (x, y, w, h), 'color': (0, 0, 255),
                                'text': f"SPOOF ({real_votes}/{HISTORY_LENGTH})", 'timer': BOX_PERSISTENCE
                            })

                    if new_drawings:
                        active_drawings = new_drawings

            except Exception: pass 

        for i in range(len(active_drawings) - 1, -1, -1):
            d = active_drawings[i]
            x, y, w, h = d['box']
            cv2.rectangle(frame, (x, y), (x + w, y + h), d['color'], 2)
            cv2.putText(frame, d['text'], (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, d['color'], 2)
            d['timer'] -= 1
            if d['timer'] <= 0: active_drawings.pop(i)

        frame_count += 1
        if ret: 
            small_frame = cv2.resize(frame, (960, 540)) 
            cv2.imshow('AttendAI Camera', small_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
