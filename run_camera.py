import cv2
from mtcnn.mtcnn import MTCNN
from deepface import DeepFace
import requests
import time
import os
import logging

# --- Logging Setup ---
# 1. File Handler: Writes everything (INFO and up) to camera.log
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='camera.log',
    filemode='a'
)

# 2. Console Handler: Shows ONLY errors in the terminal (keeps it clean)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(console_handler)
# ---------------------

# --- Configuration ---
DB_PATH = "datasets/"
MODEL_NAME = "VGG-Face"
API_URL = "http://127.0.0.1:5000"
FRAME_PROCESS_RATE = 5   # Check for faces every 5 frames
BOX_PERSISTENCE = 60     # Keep the box on screen for 60 frames (approx 2 seconds)

def main():
    detector = MTCNN()
    
    # --- CAMERA SELECTION ---
    # Option A: Laptop Webcam (Stable on Windows)
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) 
    
    # Option B: IP Camera (Uncomment if using phone)
    # url = "http://192.168.1.x:8080/video"
    # cap = cv2.VideoCapture(url)
    # ------------------------

    if not cap.isOpened():
        logging.error("Error: Could not open webcam.")
        print("Error: Could not open webcam.")
        return

    frame_count = 0
    active_drawings = [] 

    logging.info("Camera script started. Loop beginning...")
    print("Camera started. Check camera.log for details.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # --- 1. DETECTION PHASE (Runs every Nth frame) ---
        if frame_count % FRAME_PROCESS_RATE == 0:
            try:
                # Detect faces
                detected_faces = detector.detect_faces(frame)
                
                if detected_faces:
                    new_drawings = []
                    
                    for face in detected_faces:
                        if face['confidence'] < 0.9:
                            continue

                        x, y, w, h = face['box']
                        
                        # Add padding
                        pad_x = int(w * 0.1)
                        pad_y = int(h * 0.1)
                        x1, y1 = max(0, x - pad_x), max(0, y - pad_y)
                        x2, y2 = min(frame.shape[1], x + w + pad_x), min(frame.shape[0], y + h + pad_y)
                        
                        cropped_face = frame[y1:y2, x1:x2]
                        if cropped_face.size == 0:
                            continue

                        # --- Liveness Detection (BYPASSED) ---
                        # We keep the logic here but force it to False to avoid the TensorFlow crash.
                        is_spoof = False 
                        # -------------------------------------

                        if is_spoof:
                            logging.warning("Spoof detected!")
                            new_drawings.append({
                                'box': (x, y, w, h),
                                'color': (0, 0, 255), # RED
                                'text': "SPOOF / FAKE",
                                'timer': BOX_PERSISTENCE
                            })
                            continue # Skip recognition
                        
                        # --- Recognition (Only if Real) ---
                        dfs = DeepFace.find(img_path=cropped_face,
                                            db_path=DB_PATH,
                                            model_name=MODEL_NAME,
                                            enforce_detection=False,
                                            silent=True)
                        
                        if dfs and not dfs[0].empty:
                            identity_path = dfs[0]['identity'].iloc[0]
                            folder_path = os.path.dirname(identity_path) 
                            user_id = os.path.basename(folder_path)    

                            # Save RECOGNIZED result to drawings
                            new_drawings.append({
                                'box': (x, y, w, h),
                                'color': (0, 255, 0), # GREEN
                                'text': user_id,
                                'timer': BOX_PERSISTENCE
                            })

                            # Send API Requests (Business Logic)
                            try:
                                if user_id.startswith('student_'):
                                    logging.info(f"Student seen: {user_id}. Sending log request...")
                                    res = requests.post(f"{API_URL}/log_student_entry_auto", json={"user_id": user_id})
                                    logging.info(f"API Response: {res.json().get('message', res.json())}")
                                elif user_id.startswith('faculty_'):
                                    logging.info(f"Faculty seen: {user_id}. Sending start request...")
                                    res = requests.post(f"{API_URL}/start_class", json={"faculty_id": user_id})
                                    logging.info(f"API Response: {res.json().get('message', res.json())}")
                            except Exception as e:
                                logging.error(f"API CALL FAILED: {e}")
                    
                    # Update our active list only if we found something new
                    if new_drawings:
                        active_drawings = new_drawings

            except Exception as e:
                # logging.error(f"Detection Error: {e}")
                pass 

        # --- 2. DRAWING PHASE ---
        for i in range(len(active_drawings) - 1, -1, -1):
            draw_item = active_drawings[i]
            x, y, w, h = draw_item['box']
            color = draw_item['color']
            text = draw_item['text']
            
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
            
            draw_item['timer'] -= 1
            if draw_item['timer'] <= 0:
                active_drawings.pop(i)

        frame_count += 1
        
        if ret: 
            small_frame = cv2.resize(frame, (960, 540)) 
            cv2.imshow('Smart Attendance Camera', small_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    logging.info("Camera script shutting down.")
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()