# AttendAI - Smart Attendance System

AttendAI is an intelligent, automated attendance tracking system powered by facial recognition.

## Features
*   **Real-time Face Recognition**: Instantly identifies registered students and faculty.
*   **Liveness Detection**: Prevents spoofing using advanced anti-spoofing algorithms.
*   **Smart Scheduling**: Automatically links attendance to the correct class based on the current time and day.
*   **Automated Logging**:
    *   **Faculty**: Starts the class session automatically.
    *   **Students**: Logs attendance without manual intervention.
*   **Substitute Management**: Easy manual override for substitute teachers.

## Getting Started

### Prerequisites
*   Python 3.x
*   MySQL Server

### Installation
1.  Clone the repository.
2.  Install dependencies: `pip install -r requirements.txt` (if available) or manually install `flask`, `mysql-connector-python`, `opencv-python`, `deepface`, `tensorflow`, `mtcnn`.
3.  Set up the MySQL database `smart_attendance`.

### Running the System
1.  **Start Backend**:
    ```bash
    cd backend
    python app.py
    ```
2.  **Start Camera**:
    ```bash
    python run_camera.py
    ```
3.  **View Dashboard**:
    Open [http://localhost:5000](http://localhost:5000)
