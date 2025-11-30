# AttendAI - Smart Attendance System

AttendAI is an intelligent, automated attendance tracking system powered by facial recognition and AI. It streamlines the attendance process for educational institutions by using computer vision to verify identity and liveness.

## 🚀 Features

*   **Real-time Face Recognition**: Instantly identifies registered students and faculty using DeepFace and MTCNN.
*   **Liveness Detection**: Prevents spoofing (e.g., holding up a photo) using advanced anti-spoofing algorithms.
*   **Smart Scheduling**: Automatically links attendance to the correct class based on the current time and day.
*   **Automated Logging**:
    *   **Faculty**: Starts the class session automatically upon recognition.
    *   **Students**: Logs attendance as "temporary" and finalizes it after a confirmation period.
*   **Substitute Management**: Supports manual assignment of substitute teachers.
*   **Web Dashboard**: A Flask-based interface to view live status and schedules.

## 🛠️ Tech Stack

*   **Backend**: Python, Flask
*   **AI/ML**: TensorFlow, Keras, DeepFace, MTCNN, OpenCV
*   **Database**: MySQL
*   **Frontend**: HTML/CSS (Jinja2 templates)

## 📋 Prerequisites

*   Python 3.8+
*   MySQL Server
*   Webcam

## ⚙️ Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/naurjhanvi/AttendAI.git
    cd AttendAI
    ```

2.  **Install Dependencies**
    It is recommended to use a virtual environment.
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # Mac/Linux
    # source venv/bin/activate
    
    pip install -r requirements.txt
    ```

3.  **Database Setup**
    *   Ensure your MySQL server is running.
    *   Create a database named `smart_attendance`.
    *   Update the database credentials in `backend/db.py` if they differ from the defaults (`root`, no password).
    *   (Optional) Import your schema/tables (`schedules`, `classes`, `attendance_log`, `users`).

4.  **Dataset Setup**
    *   Place user images in the `datasets/` folder.
    *   Structure: `datasets/user_id/image.jpg` (e.g., `datasets/student_001/face.jpg`).

## 🏃‍♂️ Running the System

You need to run two separate processes: the backend server and the camera script.

1.  **Start the Backend Server**
    ```bash
    cd backend
    python app.py
    ```
    *The server will start at `http://localhost:5000`*

2.  **Start the Camera Script**
    Open a new terminal window:
    ```bash
    python run_camera.py
    ```
    *This will open the webcam feed and start detecting faces.*

3.  **Access the Dashboard**
    Open your browser and navigate to [http://localhost:5000](http://localhost:5000) to view the attendance dashboard.

## 📂 Project Structure

```
AttendAI/
├── backend/
│   ├── app.py              # Main Flask application
│   ├── attendance.py       # Attendance logic & DB interactions
│   ├── db.py               # Database connection config
│   └── templates/          # HTML templates
├── datasets/               # Face image database
├── run_camera.py           # Main camera & recognition script
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```
