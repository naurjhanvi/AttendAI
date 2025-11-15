from db import get_db_connection
from datetime import date, datetime

def get_active_schedule(faculty_id):
    """Finds the active class schedule based on faculty, day, and time."""
    conn = get_db_connection()
    if not conn: return {'error': 'Database connection failed'}, 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        today = datetime.now()
        current_day_mysql = today.isoweekday() % 7 + 1 
        current_time = today.strftime('%H:%M:%S')

        query = """
            SELECT schedule_id, class_id 
            FROM schedules 
            WHERE faculty_id = %s 
              AND day_of_week = %s
              AND %s BETWEEN start_time AND end_time
            LIMIT 1
        """
        cursor.execute(query, (faculty_id, current_day_mysql, current_time))
        result = cursor.fetchone()
        
        if not result:
            return {'error': 'No active class found for this faculty at this time'}, 404
        return result, 200
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cursor.close()
        conn.close()

def get_all_todays_schedules():
    """Returns a list of classes for today that HAVE NOT ENDED yet."""
    today = datetime.now()
    current_day_mysql = today.isoweekday() % 7 + 1 
    current_time = today.strftime('%H:%M:%S') # Get current time string
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # --- UPDATED QUERY: Added 'AND s.end_time >= %s' ---
        query = """
            SELECT s.schedule_id, s.start_time, s.end_time, c.class_code, c.class_name, s.faculty_id
            FROM schedules s
            JOIN classes c ON s.class_id = c.class_id
            WHERE s.day_of_week = %s
              AND s.end_time >= %s 
            ORDER BY s.start_time ASC
        """
        cursor.execute(query, (current_day_mysql, current_time))
        results = cursor.fetchall()
        
        # Convert timedeltas to strings
        for row in results:
            if 'start_time' in row and not isinstance(row['start_time'], str):
                row['start_time'] = str(row['start_time'])
            if 'end_time' in row and not isinstance(row['end_time'], str):
                row['end_time'] = str(row['end_time'])
            
        return results
    finally:
        cursor.close()
        conn.close()

def log_student_entry(user_id, schedule_id):
    """Logs a student's entry as 'temporary_present' FOR A SPECIFIC SCHEDULE."""
    if not schedule_id: return {'error': 'No active class session'}, 400

    today_date = date.today()
    conn = get_db_connection()
    if not conn: return {'error': 'DB connection failed'}, 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        # Check if confirmed
        cursor.execute("SELECT * FROM attendance_log WHERE user_id = %s AND schedule_id = %s AND log_date = %s AND status = 'final_present'", (user_id, schedule_id, today_date))
        if cursor.fetchone(): return {'message': 'Student already confirmed for this class'}, 200

        # Check if temporary
        cursor.execute("SELECT * FROM attendance_log WHERE user_id = %s AND schedule_id = %s AND log_date = %s AND status = 'temporary_present'", (user_id, schedule_id, today_date))
        if cursor.fetchone(): return {'message': 'Student already temporary for this class'}, 200

        # Log new entry
        cursor.execute("INSERT INTO attendance_log (user_id, schedule_id, status) VALUES (%s, %s, 'temporary_present')", (user_id, schedule_id))
        conn.commit()
        return {'message': f'Successfully logged {user_id} as temporary for schedule {schedule_id}'}, 201
    except Exception as e:
        conn.rollback()
        return {'error': str(e)}, 500
    finally:
        cursor.close()
        conn.close()

def confirm_attendance_for_schedule(schedule_id):
    """Updates all 'temporary_present' students to 'final_present' FOR A SPECIFIC SCHEDULE."""
    if not schedule_id: return {'error': 'No schedule ID provided'}, 400

    today_date = date.today()
    conn = get_db_connection()
    if not conn: return {'error': 'DB connection failed'}, 500
        
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE attendance_log SET status = 'final_present' WHERE schedule_id = %s AND log_date = %s AND status = 'temporary_present'", (schedule_id, today_date))
        updated_rows = cursor.rowcount
        conn.commit()
        return {'message': f'Schedule {schedule_id} confirmed. {updated_rows} students finalized.'}, 200
    except Exception as e:
        conn.rollback()
        return {'error': str(e)}, 500
    finally:
        cursor.close()
        conn.close()

def get_attendance_status():
    """Retrieves today's attendance list."""
    today_date = date.today()
    conn = get_db_connection()
    if not conn: return {'error': 'DB connection failed'}, 500
        
    cursor = conn.cursor(dictionary=True)
    try:
        query_select = """
            SELECT al.user_id, al.status, al.log_time, c.class_code 
            FROM attendance_log al
            JOIN schedules s ON al.schedule_id = s.schedule_id
            JOIN classes c ON s.class_id = c.class_id
            WHERE al.log_date = %s
            ORDER BY al.log_time DESC
        """
        cursor.execute(query_select, (today_date,))
        records = cursor.fetchall()
        
        # Fix datetime serialization
        for row in records:
            if 'log_time' in row and not isinstance(row['log_time'], str):
                row['log_time'] = row['log_time'].isoformat()
            
        return records, 200
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cursor.close()
        conn.close()