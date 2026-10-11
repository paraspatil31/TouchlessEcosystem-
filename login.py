# === Face Recognition Login Integration ===
import os
import numpy as np
import cv2
# Register face images and store them in 'faces/'
def register_face(user_id):
    cap = cv2.VideoCapture(0)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    count = 0
    os.makedirs("faces", exist_ok=True)

    while count < 20:
        ret, frame = cap.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            count += 1
            face_img = gray[y:y+h, x:x+w]
            cv2.imwrite(f"faces/user_{user_id}_{count}.jpg", face_img)
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

        cv2.imshow("Register Face", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
#register_face(2)  # Example user_id, replace with actual user ID
def train_face_recognizer():
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    faces, ids = [], []

    for filename in os.listdir("faces"):
        img_path = os.path.join("faces", filename)
        gray = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        faces.append(gray)
        ids.append(int(filename.split("_")[1]))

    recognizer.train(faces, np.array(ids))
    recognizer.save("trainer.yml")
    print("Face recognizer trained successfully.")
train_face_recognizer()



#     speech(f"Face data for user {user_id} captured successfully.")


# # Train the face recognizer using collected images
# def train_face_recognizer():
#     recognizer = cv2.face.LBPHFaceRecognizer_create()
#     faces, ids = [], []

#     for filename in os.listdir("faces"):
#         img_path = os.path.join("faces", filename)
#         gray = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
#         faces.append(gray)
#         ids.append(int(filename.split("_")[1]))

#     recognizer.train(faces, np.array(ids))
#     recognizer.save("trainer.yml")
#     speech("Face recognizer trained successfully.")


# # Face login using the trained recognizer
# def face_login():
#     try:
#         recognizer = cv2.face.LBPHFaceRecognizer_create()
#         recognizer.read("trainer.yml")
#         face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

#         cap = cv2.VideoCapture(0)
#         authenticated = False

#         while not authenticated:
#             ret, frame = cap.read()
#             gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#             faces = face_cascade.detectMultiScale(gray, 1.3, 5)

#             for (x, y, w, h) in faces:
#                 id_, conf = recognizer.predict(gray[y:y+h, x:x+w])
#                 if conf < 70:
#                     speech(f"Welcome User {id_}")
#                     authenticated = True
#                     doctor_mode()  # You can route this based on id_
#                     break

#             cv2.imshow("Face Login", frame)
#             if cv2.waitKey(1) & 0xFF == ord('q'):
#                 break

#         cap.release()
#         cv2.destroyAllWindows()

#     except Exception as e:
#         speech("Face login failed. Please check camera or training data.")
#         print(f"Error during face login: {e}")


# # === UI Hook ===
# # Add this inside your main GUI button frame
# # login_button = ttk.Button(button_frame, text="Face Login", command=face_login, width=15)
# # login_button.pack(side="left", padx=20, pady=15)

# # === Registration and Training Example ===
# # To be used from a developer/admin interface only
# # register_face(1)
# # train_face_recognizer()

# # This module is now integrated for facial recognition login.
# # You can dynamically assign roles like doctor_mode() or patient_mode() based on user id or role stored in DB.
