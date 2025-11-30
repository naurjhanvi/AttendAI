import logging
import threading
import time
from logging import FileHandler
from flask import Flask, jsonify, request, render_template
from db import get_db_connection 
from attendance import (
    log_student_entry, 
    confirm_attendance_for_schedule, 
    get_attendance_status, 
    get_active_schedule,
    get_all_todays_schedules
)

CONFIRMATION_DELAY_SECONDS = 30 

file_handler = FileHandler('backend.log', encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))

app = Flask(__name__)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

CURRENT_ACTIVE_SCHEDULE_ID = None
CURRENT_ACTIVE_FACULTY_ID = None
PENDING_SUBSTITUTE = None
ACTIVE_TIMERS = {}

def background_auto_finalize(schedule_id):
    try:
        app.logger.info(f"⏱️ Auto-Finalize Timer for Schedule {schedule_id} started. Waiting {CONFIRMATION_DELAY_SECONDS} seconds...")
        time.sleep(CONFIRMATION_DELAY_SECONDS)
        
        with app.app_context():
            app.logger.info(f"⏰ Time's up! Auto-finalizing attendance for Schedule {schedule_id}...")
            response, _ = confirm_attendance_for_schedule(schedule_id)
            
            app.logger.info(f"✅ Auto-Finalize Complete: {response.get('message')}")
            
            if schedule_id in ACTIVE_TIMERS:
                del ACTIVE_TIMERS[schedule_id]
    except Exception as e:
        with app.app_context():
            app.logger.error(f"Error in background_auto_finalize: {e}")

@app.route('/', methods=['GET'])
def dashboard():
    return render_template('index.html')

@app.route('/start_class', methods=['POST'])
def api_start_class():
    global CURRENT_ACTIVE_SCHEDULE_ID, CURRENT_ACTIVE_FACULTY_ID, PENDING_SUBSTITUTE, ACTIVE_TIMERS
    
    data = request.get_json()
    if not data or 'faculty_id' not in data:
        return jsonify({'error': 'Missing faculty_id'}), 400

    faculty_id_from_camera = data['faculty_id']

    if faculty_id_from_camera == CURRENT_ACTIVE_FACULTY_ID:
        return jsonify({'message': f'Class {CURRENT_ACTIVE_SCHEDULE_ID} is in session. Timer is running.'}), 200
    
    new_schedule_id = None
    new_faculty_id = None
    
    if PENDING_SUBSTITUTE is not None and faculty_id_from_camera == PENDING_SUBSTITUTE['faculty_id']:
        app.logger.info(f"Substitute {faculty_id_from_camera} verified by camera.")
        new_schedule_id = PENDING_SUBSTITUTE['schedule_id']
        new_faculty_id = PENDING_SUBSTITUTE['faculty_id']
        PENDING_SUBSTITUTE = None 

    else:
        schedule_details, status_code = get_active_schedule(faculty_id_from_camera)
        if status_code == 200:
            app.logger.info(f"Regularly scheduled faculty {faculty_id_from_camera} seen.")
            new_schedule_id = schedule_details['schedule_id']
            new_faculty_id = faculty_id_from_camera
        else:
            app.logger.info(f"Faculty {faculty_id_from_camera} seen, but has no active/pending schedule. Ignoring.")
            return jsonify({'message': f'Faculty {faculty_id_from_camera} seen, but has no active schedule. No action taken.'}), 200

    CURRENT_ACTIVE_SCHEDULE_ID = new_schedule_id
    CURRENT_ACTIVE_FACULTY_ID = new_faculty_id
    
    if new_schedule_id not in ACTIVE_TIMERS:
        app.logger.info(f"Starting new auto-finalize timer for {new_schedule_id}.")
        t = threading.Thread(target=background_auto_finalize, args=(new_schedule_id,))
        t.daemon = True 
        t.start()
        ACTIVE_TIMERS[new_schedule_id] = t
        return jsonify({'message': f'Class {new_schedule_id} started. Auto-finalize timer running.'}), 200
    else:
        app.logger.info(f"Class {new_schedule_id} resumed. Timer is already running.")
        return jsonify({'message': f'Class {new_schedule_id} resumed. Timer already running.'}), 200


@app.route('/log_student_entry_auto', methods=['POST'])
def api_log_student_auto():
    data = request.get_json()
    if not data or 'user_id' not in data: return jsonify({'error': 'Missing user_id'}), 400
    
    response, status_code = log_student_entry(data['user_id'], CURRENT_ACTIVE_SCHEDULE_ID)
    if status_code == 201: app.logger.info(response.get('message'))
    return jsonify(response), status_code

@app.route('/status', methods=['GET'])
def api_get_status():
    response, status_code = get_attendance_status()
    return jsonify(response), status_code

@app.route('/get_schedules', methods=['GET'])
def api_get_schedules():
    response, status_code = get_all_todays_schedules()
    return jsonify(response), status_code

@app.route('/assign_substitute', methods=['POST'])
def api_assign_substitute():
    global PENDING_SUBSTITUTE
    data = request.get_json()
    if not 'schedule_id' in data or not 'faculty_id' in data: return jsonify({'error': 'Missing data'}), 400

    PENDING_SUBSTITUTE = {'schedule_id': data['schedule_id'], 'faculty_id': data['faculty_id']}
    app.logger.info(f"Pending substitute request queued: {PENDING_SUBSTITUTE}")
    return jsonify({'message': 'Request received. Please look at the camera to confirm.'}), 200

@app.route('/current_session_status', methods=['GET'])
def api_session_status():
    return jsonify({
        'active': CURRENT_ACTIVE_SCHEDULE_ID is not None,
        'faculty': CURRENT_ACTIVE_FACULTY_ID,
        'schedule_id': CURRENT_ACTIVE_SCHEDULE_ID
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)