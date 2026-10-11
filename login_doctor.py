# === Face Recognition Login Integration (Doctors & Patients) ===
import os
import numpy as np
import cv2
import mysql.connector
# Register face images and store them in 'faces/'
def register_face(user_id, is_doctor=False):
    cap = cv2.VideoCapture(0)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    count = 0
    folder = "doctor_faces" if is_doctor else "faces"
    os.makedirs(folder, exist_ok=True)

    while count < 20:
        ret, frame = cap.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            count += 1
            face_img = gray[y:y+h, x:x+w]
            cv2.imwrite(f"{folder}/user_{user_id}_{count}.jpg", face_img)
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

        cv2.imshow("Register Face", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    #speech(f"Face data for {'Doctor' if is_doctor else 'Patient'} {user_id} captured successfully.")

# register_face(user_id=1, is_doctor=True)  # Doctor

# Train the face recognizer using collected images
def train_face_recognizer(is_doctor=False):
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    faces, ids = [], []
    folder = "doctor_faces" if is_doctor else "faces"

    for filename in os.listdir(folder):
        img_path = os.path.join(folder, filename)
        gray = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        faces.append(gray)
        ids.append(int(filename.split("_")[1]))

    model_path = "trainer_doctor.yml" if is_doctor else "trainer.yml"
    recognizer.train(faces, np.array(ids))
    recognizer.save(model_path)
    #speech(f"{'Doctor' if is_doctor else 'Patient'} face recognizer trained successfully.")
# train_face_recognizer(is_doctor=True)  # Doctor

# Check if user is doctor
def connect_database():
    return mysql.connector.connect(
        host="localhost",
        user="root",  # Change if needed
        passwd="1234",  # Change to your MySQL password
        database="HospitalDB"
    )

def check_if_doctor(user_id):
    conn = connect_database()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, name FROM Doctors WHERE id = %s", (user_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


# Face login with callback
def face_login(callback_on_success=None, is_doctor=False):
    try:
        model_path = "trainer_doctor.yml" if is_doctor else "trainer.yml"
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read(model_path)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        cap = cv2.VideoCapture(0)
        authenticated = False

        while not authenticated:
            ret, frame = cap.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in faces:
                id_, conf = recognizer.predict(gray[y:y+h, x:x+w])
                if conf < 70:
                   # speech(f"Welcome User {id_}")
                    authenticated = True
                    cap.release()
                    cv2.destroyAllWindows()
                    if callback_on_success:
                        callback_on_success(user_id=id_)
                    return

            cv2.imshow("Face Login", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

    except Exception as e:
        #speech("Face login failed. Please check camera or training data.")
        print(f"Error during face login: {e}")


# Doctor Mode with Face Login
# def face_login_doctor_mode():
#     def on_success(user_id):
#         doctor_info = check_if_doctor(user_id)
#         if doctor_info:
#             speech(f"Welcome Dr. {doctor_info[1]}")
#             doctor_mode()
#         else:
#             speech("Access denied. You are not registered as a doctor.")
#             messagebox.showerror("Access Denied", "This user is not registered as a doctor.")

#     face_login(callback_on_success=on_success, is_doctor=True)


# === UI Button Hook ===
# Replace Patient Mode button:
# patient_button = ttk.Button(button_frame, text="Patient Mode", command=lambda: face_login(callback_on_success=patient_mode), width=15)

# Replace Doctor Mode button:
# doctor_button = ttk.Button(button_frame, text="Doctor Mode", command=face_login_doctor_mode, width=15)


# === Admin Registration Example ===
# register_face(user_id=1, is_doctor=False)  # Patient
# train_face_recognizer(is_doctor=False)

# register_face(user_id=101, is_doctor=True)  # Doctor
# train_face_recognizer(is_doctor=True)
