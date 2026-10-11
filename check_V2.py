import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import speech_recognition as sr
import pywhatkit as kit
import pyttsx3
import time
from PIL import Image, ImageTk
import logging
import cv2
import mediapipe as mp
import pyautogui
import math
import sqlite3
import webbrowser
import mysql.connector
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
global Phone_Number = "Your Phone Number"

face_scan_status = None  # Declare globally
def update_face_scan_status(text, color):
    if face_scan_status:
        face_scan_status.config(text=text, fg=color)
        root.update_idletasks()

# Face login using the trained recognizer
# Face login with callback
def face_login(callback_on_success=None, is_doctor=False):
    try:
        update_face_scan_status("Face Scanning...", "blue")

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
                    speech(f"Welcome User {id_}")
                    authenticated = True
                    cap.release()
                    cv2.destroyAllWindows()
                    if callback_on_success:
                        callback_on_success(user_id=id_)
                    update_face_scan_status("Idle", "black")
                    return

            cv2.imshow("Face Login", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                update_face_scan_status("Idle", "black")
                break

        cap.release()
        cv2.destroyAllWindows()

    except Exception as e:
        speech("Face login failed. Please check camera or training data.")
        print(f"Error during face login: {e}")



def connect_database():
    return mysql.connector.connect(
        host="localhost",
        user="root",  # Change if needed
        passwd="1234",  # Change to your MySQL password
        database="HospitalDB"
    )


# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
engine = pyttsx3.init()
# Initialize Speech Engine
def speech(text):
    if engine._inLoop:
        engine.endLoop()  # Stop the previous loop if already running
    logging.info(f"Speaking: {text}")
    print(text)
    engine = pyttsx3.init()  # Reinitialize engine each time to prevent errors
    engine.say(text)
    engine.runAndWait()

# Initialize the database
def initialize_database():
    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()

    # Create Patients table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            discharge_date TEXT
        )
    ''')

    # Create Records table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            diagnosis TEXT,
            prescription TEXT,
            FOREIGN KEY (patient_id) REFERENCES Patients (id)
        )
    ''')

    conn.commit()
    conn.close()

# Function to add a patient
def add_patient(name, age, discharge_date):
    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO Patients (name, age, discharge_date) VALUES (?, ?, ?)', (name, age, discharge_date))
    conn.commit()
    conn.close()

# Function to add a medical record
def get_patient_records(patient_id):
    conn = connect_database()  # Connect to MySQL database
    cursor = conn.cursor()
    
    # Fetch patient details with explicit column selection
    cursor.execute("""
        SELECT 
            id,
            name,
            age,
            disease,
            doctor_id,
            DATE_FORMAT(joining_date, '%Y-%m-%d') as joining_date,
            DATE_FORMAT(discharge_date, '%Y-%m-%d') as discharge_date
        FROM Patients 
        WHERE id = %s
    """, (patient_id,))
    patient = cursor.fetchone()
    
    # Fetch doctor details if patient exists
    doctor = None
    if patient and patient[4]:  # if patient exists and has a doctor_id
        cursor.execute("SELECT * FROM Doctors WHERE id = %s", (patient[4],))
        doctor = cursor.fetchone()
    
    conn.close()
    return patient, doctor

def view_patient_records(doctor_window):
    conn = connect_database()
    cursor = conn.cursor()

    try:
        # Fetch all patients
        cursor.execute("SELECT id, name FROM Patients")
        patients = cursor.fetchall()

        if not patients:
            messagebox.showinfo("Info", "No patients found.", parent=doctor_window)
            return

        # Create a new fullscreen window
        patient_list_window = tk.Toplevel(doctor_window)
        patient_list_window.title("Select Patient")
        patient_list_window.attributes('-fullscreen', True)

        # Title
        tk.Label(patient_list_window, text="Patient Records", font=("Arial", 32, "bold"), fg="blue", bg="white").pack(pady=30)

        # Create frame for treeview
        frame = ttk.Frame(patient_list_window)
        frame.pack(expand=True, fill='both', padx=50, pady=20)

        # Create a treeview
        tree = ttk.Treeview(frame, columns=("ID", "Name"), show="headings")
        tree.heading("ID", text="Patient ID")
        tree.heading("Name", text="Patient Name")
        tree.column("ID", width=150, anchor='center')
        tree.column("Name", width=400, anchor='w')

        # Add vertical scrollbar
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        tree.pack(expand=True, fill='both')

        for patient in patients:
            tree.insert('', 'end', values=patient)

        def view_selected_patient():
            selected_item = tree.focus()
            if selected_item:
                patient_id = tree.item(selected_item)['values'][0]
                patient, doctor = get_patient_records(patient_id)
                if patient:
                    display_patient_data(patient, doctor)
                else:
                    messagebox.showinfo("Error", "No record found for this patient.", parent=patient_list_window)
            else:
                messagebox.showwarning("Warning", "Please select a patient.", parent=patient_list_window)

        # View Record Button
        button_frame = ttk.Frame(patient_list_window)
        button_frame.pack(pady=30)

        ttk.Button(button_frame, text="View Record", command=view_selected_patient, width=20).pack(side='left', padx=20)
        ttk.Button(button_frame, text="Close", command=patient_list_window.destroy, width=20).pack(side='left', padx=20)

        # ESC key to exit fullscreen
        patient_list_window.bind("<Escape>", lambda e: patient_list_window.attributes('-fullscreen', False))

    finally:
        cursor.close()
        conn.close()

def display_patient_data(patient, doctor):
    record_window = tk.Toplevel()
    record_window.title("Patient Record")
    record_window.attributes('-fullscreen', True)
    
    # Create main frame
    main_frame = ttk.Frame(record_window, padding="20")
    main_frame.pack(expand=True, fill='both')
    
    # Configure style for tables
    style = ttk.Style()
    style.configure("Custom.Treeview",
                   font=('Helvetica', 12),
                   rowheight=30,
                   background="#f0f0f0",
                   fieldbackground="#f0f0f0",
                   foreground="#333333")
    
    style.configure("Custom.Treeview.Heading",
                   font=('Helvetica', 12, 'bold'),
                   background="#4a90e2",
                   foreground="white",
                   padding=(10, 5))
    
    style.map("Custom.Treeview",
              background=[('selected', '#4a90e2')],
              foreground=[('selected', 'white')])
    
    # Create frame for tables with a nice background
    table_frame = ttk.Frame(main_frame, style='Card.TFrame')
    table_frame.pack(expand=True, fill='both', padx=20, pady=20)
    
    # Patient Information Table
    patient_frame = ttk.LabelFrame(table_frame, text="Patient Information", padding="10",
                                 style='Custom.TLabelframe')
    patient_frame.pack(fill='both', expand=True, pady=(0, 20))
    
    # Create patient table with scrollbar
    patient_tree = ttk.Treeview(patient_frame, style="Custom.Treeview", height=6)
    patient_scroll = ttk.Scrollbar(patient_frame, orient="vertical", command=patient_tree.yview)
    patient_tree.configure(yscrollcommand=patient_scroll.set)
    
    # Configure patient table
    patient_tree['columns'] = ('Value')
    patient_tree.column('#0', width=250, anchor='w')
    patient_tree.column('Value', width=500, anchor='w')
    patient_tree.heading('#0', text='Field')
    patient_tree.heading('Value', text='Information')
    
    # Insert patient data with alternating colors
    patient_data = [
        ("Patient ID", str(patient[0])),
        ("Name", patient[1]),
        ("Age", str(patient[2])),
        ("Disease", patient[3]),
        ("Joining Date", str(patient[5]) if patient[5] else "Not Set"),
        ("Discharge Date", str(patient[6]) if patient[6] else "Not Set")
    ]
    
    for i, (field, value) in enumerate(patient_data):
        tag = 'evenrow' if i % 2 == 0 else 'oddrow'
        patient_tree.insert('', 'end', text=field, values=(value,), tags=(tag,))
    
    patient_tree.tag_configure('oddrow', background='#e8f4fc')
    patient_tree.tag_configure('evenrow', background='#ffffff')
    
    # Pack patient table
    patient_tree.pack(side='left', fill='both', expand=True)
    patient_scroll.pack(side='right', fill='y')
    
    # Doctor Information Table (if doctor exists)
    if doctor:
        doctor_frame = ttk.LabelFrame(table_frame, text="Doctor Information", padding="10",
                                    style='Custom.TLabelframe')
        doctor_frame.pack(fill='both', expand=True)
        
        doctor_tree = ttk.Treeview(doctor_frame, style="Custom.Treeview", height=4)
        doctor_scroll = ttk.Scrollbar(doctor_frame, orient="vertical", command=doctor_tree.yview)
        doctor_tree.configure(yscrollcommand=doctor_scroll.set)
        
        doctor_tree['columns'] = ('Value')
        doctor_tree.column('#0', width=250, anchor='w')
        doctor_tree.column('Value', width=500, anchor='w')
        doctor_tree.heading('#0', text='Field')
        doctor_tree.heading('Value', text='Information')
        
        doctor_data = [
            ("Doctor Name", doctor[1]),
            ("Specialization", doctor[2]),
            ("Contact", doctor[3]),
            ("Email", doctor[4])
        ]
        
        for i, (field, value) in enumerate(doctor_data):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            doctor_tree.insert('', 'end', text=field, values=(value,), tags=(tag,))
        
        doctor_tree.tag_configure('oddrow', background='#e8f4fc')
        doctor_tree.tag_configure('evenrow', background='#ffffff')
        
        doctor_tree.pack(side='left', fill='both', expand=True)
        doctor_scroll.pack(side='right', fill='y')
    
    # Configure style for close button
    style.configure("Exit.TButton",
                   font=('Helvetica', 14, 'bold'),
                   padding=15,
                   background="#ff4d4d",
                   foreground="white")
    
    style.map("Exit.TButton",
              background=[('active', '#ff1a1a')],
              foreground=[('active', 'white')])
    
    # Create a frame for the close button
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(pady=30)
    
    # Close button with improved styling
   

    ttk.Button(main_frame, text="Close", 
               command=record_window.destroy,
               style="Close.TButton").pack(pady=20)




def prescribe_medicine(doctor_window):
    conn = connect_database()
    cursor = conn.cursor()

    try:
        # Fetch all patients
        cursor.execute("SELECT id, name FROM Patients")
        patients = cursor.fetchall()

        if not patients:
            messagebox.showinfo("Info", "No patients found.", parent=doctor_window)
            return

        # Create fullscreen window
        prescribe_list_window = tk.Toplevel(doctor_window)
        prescribe_list_window.title("Select Patient for Prescription")
        prescribe_list_window.attributes('-fullscreen', True)

        tk.Label(prescribe_list_window, text="Prescribe Medicine", font=("Arial", 32, "bold"), fg="purple", bg="white").pack(pady=30)

        frame = ttk.Frame(prescribe_list_window)
        frame.pack(expand=True, fill='both', padx=50, pady=20)

        tree = ttk.Treeview(frame, columns=("ID", "Name"), show="headings")
        tree.heading("ID", text="Patient ID")
        tree.heading("Name", text="Patient Name")
        tree.column("ID", width=150, anchor='center')
        tree.column("Name", width=400, anchor='w')

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        tree.pack(expand=True, fill='both')

        for patient in patients:
            tree.insert('', 'end', values=patient)

        def prescribe_selected_patient():
            selected_item = tree.focus()
            if selected_item:
                patient_id = tree.item(selected_item)['values'][0]
                
                prescription = simpledialog.askstring("Input", "Enter Prescription Details:", parent=prescribe_list_window)
                if not prescription:
                    return

                conn2 = connect_database()
                cursor2 = conn2.cursor()
                cursor2.execute(
                    "INSERT INTO Records (patient_id, diagnosis, prescription) VALUES (%s, %s, %s)",
                    (patient_id, "N/A", prescription)
                )
                conn2.commit()
                conn2.close()

                messagebox.showinfo("Success", "Medicine Prescribed Successfully!", parent=prescribe_list_window)
                speech("Medicine prescribed successfully.")
            else:
                messagebox.showwarning("Warning", "Please select a patient.", parent=prescribe_list_window)

        # Buttons
        button_frame = ttk.Frame(prescribe_list_window)
        button_frame.pack(pady=30)

        ttk.Button(button_frame, text="Prescribe Medicine", command=prescribe_selected_patient, width=20).pack(side='left', padx=20)
        ttk.Button(button_frame, text="Close", command=prescribe_list_window.destroy, width=20).pack(side='left', padx=20)

        # ESC to exit fullscreen
        prescribe_list_window.bind("<Escape>", lambda e: prescribe_list_window.attributes('-fullscreen', False))

    finally:
        cursor.close()
        conn.close()



def schedule_appointment(doctor_window):
    patient_id = simpledialog.askinteger("Input", "Enter Patient ID:",parent=doctor_window)
    if not patient_id:
        return
    
    appointment_date = simpledialog.askstring("Input", "Enter Appointment Date (YYYY-MM-DD):",parent=doctor_window)
    if not appointment_date:
        return
    
    conn = connect_database()
    cursor = conn.cursor()
    
    # Assuming there's an "Appointments" table
    cursor.execute("INSERT INTO Appointments (patient_id, date) VALUES (%s, %s)", 
                   (patient_id, appointment_date))
    
    conn.commit()
    conn.close()
    
    messagebox.showinfo("Success", "Appointment Scheduled Successfully!",parent=doctor_window)
    speech(f"Appointment scheduled on {appointment_date}.")






def analyze_medical_reports(doctor_window):
    patient_id = simpledialog.askinteger("Input", "Enter Patient ID:",parent=doctor_window)
    if not patient_id:
        return
    
    conn = connect_database()
    cursor = conn.cursor()
    
    try:
        # First check if patient exists
        cursor.execute("""
            SELECT name, age, disease 
            FROM Patients 
            WHERE id = %s
        """, (patient_id,))
        patient_info = cursor.fetchone()
        
        if not patient_info:
            messagebox.showinfo("Error", "Patient not found!", parent=doctor_window)
            return
        
        # Modified query to handle records
        cursor.execute("""
            SELECT r.prescription, r.diagnosis, 
                   IFNULL(DATE_FORMAT(r.record_date, '%Y-%m-%d'), 
                         DATE_FORMAT(CURRENT_TIMESTAMP, '%Y-%m-%d')) as record_date
            FROM Records r
            WHERE r.patient_id = %s
            ORDER BY r.record_date DESC
        """, (patient_id,))
        records = cursor.fetchall()
        
        # Create report window
        report_window = tk.Toplevel(doctor_window)
        report_window.title(f"Medical Report - Patient {patient_id}")
        report_window.geometry("1000x700")
        
        # Patient info frame
        info_frame = ttk.LabelFrame(report_window, text="Patient Information", padding="20")
        info_frame.pack(fill='x', padx=20, pady=10)
        
        info_style = {'font': ('Helvetica', 12), 'pady': 5}
        ttk.Label(info_frame, text=f"Name: {patient_info[0]}", **info_style).pack(anchor='w')
        ttk.Label(info_frame, text=f"Age: {patient_info[1]}", **info_style).pack(anchor='w')
        ttk.Label(info_frame, text=f"Current Disease: {patient_info[2]}", **info_style).pack(anchor='w')
        
        # Records frame
        records_frame = ttk.LabelFrame(report_window, text="Medical Records History", padding="20")
        records_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Create treeview
        tree = ttk.Treeview(records_frame, columns=("Date", "Diagnosis", "Prescription"), show="headings", height=15)
        
        tree.heading("Date", text="Date")
        tree.heading("Diagnosis", text="Diagnosis")
        tree.heading("Prescription", text="Prescription")
        
        tree.column("Date", width=150, anchor='center')
        tree.column("Diagnosis", width=300, anchor='w')
        tree.column("Prescription", width=400, anchor='w')
        
        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(records_frame, orient="vertical", command=tree.yview)
        x_scrollbar = ttk.Scrollbar(records_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        y_scrollbar.pack(side="right", fill="y")
        x_scrollbar.pack(side="bottom", fill="x")
        
        # Insert records
        if records:
            for record in records:
                tree.insert("", "end", values=(
                    record[2],  # Date
                    record[1] if record[1] else "N/A",  # Diagnosis
                    record[0] if record[0] else "N/A"   # Prescription
                ))
        else:
            ttk.Label(records_frame, 
                     text="No medical records found for this patient", 
                     font=('Helvetica', 11, 'italic')).pack(pady=20)
        
        # Close button
        ttk.Button(report_window, 
                   text="Close", 
                   command=report_window.destroy,
                   style="Exit.TButton").pack(pady=20)
        
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"An error occurred: {err}", parent=doctor_window)
    finally:
        cursor.close()
        conn.close()




def urgent_help(doctor_window):
    kit.sendwhatmsg_instantly(Phone_Number, "There is Emergency..!")
    speech("Urgent Help triggered! Contacting emergency team.")



# Function to listen for voice commands
# Global mic status label
mic_status = None  # Declare globally

3# Optimize speech recognition settings
def listen_for_command(prompt, options, mic_status_label):
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 0.3  # Reduced from 0.5
    recognizer.energy_threshold = 3000  # Reduced threshold for faster detection
    recognizer.dynamic_energy_threshold = False  # Disable dynamic threshold for speed

    with sr.Microphone() as source:
        def update_status(text, color):
            root.after(0, lambda: mic_status_label.config(text=text, fg=color))

        update_status("🎤 Listening...", "red")

        try:
            if prompt:
                speech(prompt)
                time.sleep(0.3)  # Reduced delay
            recognizer.adjust_for_ambient_noise(source, duration=0.1)  # Reduced duration
            audio = recognizer.listen(source, timeout=3, phrase_time_limit=2)  # Reduced timeouts

            update_status("Processing...", "blue")
            command = recognizer.recognize_google(audio).lower()
            
            # Fast command processing
            for option, action in options.items():
                if option in command:
                    update_status("Executing...", "green")
                    if isinstance(action, tuple):
                        action[1]()
                    else:
                        action()
                    update_status("Idle", "black")
                    threading.Thread(target=listen_for_command, args=("", options, mic_status_label), daemon=True).start()
                    return

            speech("Command not recognized")

        except sr.UnknownValueError:
            pass
        except sr.RequestError:
            speech("Network error")

        update_status("Idle", "black")
        threading.Thread(target=listen_for_command, args=("", options, mic_status_label), daemon=True).start()

# Optimize speech engine
def speech(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 180)  # Increase speech rate
    engine.setProperty('volume', 0.9)
    engine.say(text)
    engine.runAndWait()
    del engine  # Clean up engine after use

# Optimize database connections
def connect_database():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="1234",
        database="HospitalDB",
        buffered=True,  # Enable buffered cursors
        pool_size=5  # Connection pooling
    )


# Initialize the database
def initialize_database():
    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()

    # Create Patients table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            discharge_date TEXT
        )
    ''')

    # Create Records table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            diagnosis TEXT,
            prescription TEXT,
            FOREIGN KEY (patient_id) REFERENCES Patients (id)
        )
    ''')

    conn.commit()
    conn.close()

# Function to add a patient
def add_patient(name, age, discharge_date):
    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO Patients (name, age, discharge_date) VALUES (?, ?, ?)', (name, age, discharge_date))
    conn.commit()
    conn.close()

# Function to add a medical record
def get_patient_records(patient_id):
    conn = connect_database()  # Connect to MySQL database
    cursor = conn.cursor()
    
    # Fetch patient details with column names for clarity
    cursor.execute("""
        SELECT p.id, p.name, p.age, p.disease, p.doctor_id, p.joining_date, p.discharge_date 
        FROM Patients p 
        WHERE p.id = %s
    """, (patient_id,))
    patient = cursor.fetchone()
    
    # Fetch doctor details if patient exists
    doctor = None
    if patient and patient[4]:  # if patient exists and has a doctor_id
        cursor.execute("SELECT * FROM Doctors WHERE id = %s", (patient[4],))
        doctor = cursor.fetchone()
    
    conn.close()
    return patient, doctor



def schedule_appointment(doctor_window):
    conn = connect_database()
    cursor = conn.cursor()

    try:
        # Fetch all patients
        cursor.execute("SELECT id, name FROM Patients")
        patients = cursor.fetchall()

        if not patients:
            messagebox.showinfo("Info", "No patients found.", parent=doctor_window)
            return

        # Create fullscreen window
        schedule_list_window = tk.Toplevel(doctor_window)
        schedule_list_window.title("Select Patient for Appointment")
        schedule_list_window.attributes('-fullscreen', True)

        tk.Label(schedule_list_window, text="Schedule Appointment", font=("Arial", 32, "bold"), fg="darkgreen", bg="white").pack(pady=30)

        frame = ttk.Frame(schedule_list_window)
        frame.pack(expand=True, fill='both', padx=50, pady=20)

        tree = ttk.Treeview(frame, columns=("ID", "Name"), show="headings")
        tree.heading("ID", text="Patient ID")
        tree.heading("Name", text="Patient Name")
        tree.column("ID", width=150, anchor='center')
        tree.column("Name", width=400, anchor='w')

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        tree.pack(expand=True, fill='both')

        for patient in patients:
            tree.insert('', 'end', values=patient)

        def schedule_selected_patient():
            selected_item = tree.focus()
            if selected_item:
                patient_id = tree.item(selected_item)['values'][0]

                appointment_date = simpledialog.askstring(
                    "Input",
                    "Enter Appointment Date (YYYY-MM-DD):",
                    parent=schedule_list_window
                )
                if not appointment_date:
                    return

                conn2 = connect_database()
                cursor2 = conn2.cursor()

                # Assuming there's an "Appointments" table
                cursor2.execute(
                    "INSERT INTO Appointments (patient_id, date) VALUES (%s, %s)",
                    (patient_id, appointment_date)
                )

                conn2.commit()
                conn2.close()

                messagebox.showinfo("Success", "Appointment Scheduled Successfully!", parent=schedule_list_window)
                speech(f"Appointment scheduled on {appointment_date}.")
            else:
                messagebox.showwarning("Warning", "Please select a patient.", parent=schedule_list_window)

        # Buttons
        button_frame = ttk.Frame(schedule_list_window)
        button_frame.pack(pady=30)

        ttk.Button(button_frame, text="Schedule Appointment", command=schedule_selected_patient, width=20).pack(side='left', padx=20)
        ttk.Button(button_frame, text="Close", command=schedule_list_window.destroy, width=20).pack(side='left', padx=20)

        # ESC key exits fullscreen
        schedule_list_window.bind("<Escape>", lambda e: schedule_list_window.attributes('-fullscreen', False))

    finally:
        cursor.close()
        conn.close()


def analyze_medical_reports(doctor_window):
    conn = connect_database()
    cursor = conn.cursor()

    try:
        # Fetch all patients
        cursor.execute("SELECT id, name FROM Patients")
        patients = cursor.fetchall()

        if not patients:
            messagebox.showinfo("Info", "No patients found.", parent=doctor_window)
            return

        # Create fullscreen window
        analyze_list_window = tk.Toplevel(doctor_window)
        analyze_list_window.title("Select Patient for Medical Report")
        analyze_list_window.attributes('-fullscreen', True)

        tk.Label(analyze_list_window, text="Analyze Medical Reports", font=("Arial", 32, "bold"), fg="green", bg="white").pack(pady=30)

        frame = ttk.Frame(analyze_list_window)
        frame.pack(expand=True, fill='both', padx=50, pady=20)

        tree = ttk.Treeview(frame, columns=("ID", "Name"), show="headings")
        tree.heading("ID", text="Patient ID")
        tree.heading("Name", text="Patient Name")
        tree.column("ID", width=150, anchor='center')
        tree.column("Name", width=400, anchor='w')

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        tree.pack(expand=True, fill='both')

        for patient in patients:
            tree.insert('', 'end', values=patient)

        def analyze_selected_patient():
            selected_item = tree.focus()
            if selected_item:
                patient_id = tree.item(selected_item)['values'][0]
                show_patient_medical_report(patient_id, analyze_list_window)
            else:
                messagebox.showwarning("Warning", "Please select a patient.", parent=analyze_list_window)

        # Analyze and Close buttons
        button_frame = ttk.Frame(analyze_list_window)
        button_frame.pack(pady=30)

        ttk.Button(button_frame, text="Analyze Report", command=analyze_selected_patient, width=20).pack(side='left', padx=20)
        ttk.Button(button_frame, text="Close", command=analyze_list_window.destroy, width=20).pack(side='left', padx=20)

        # ESC key exits fullscreen
        analyze_list_window.bind("<Escape>", lambda e: analyze_list_window.attributes('-fullscreen', False))

    finally:
        cursor.close()
        conn.close()

def show_patient_medical_report(patient_id, parent_window):
    conn = connect_database()
    cursor = conn.cursor()

    try:
        # Fetch patient basic info
        cursor.execute("""
            SELECT name, age, disease 
            FROM Patients 
            WHERE id = %s
        """, (patient_id,))
        patient_info = cursor.fetchone()

        if not patient_info:
            messagebox.showinfo("Error", "Patient not found!", parent=parent_window)
            return

        # Fetch records
        cursor.execute("""
            SELECT prescription, diagnosis, 
                   DATE_FORMAT(record_date, '%Y-%m-%d') as record_date
            FROM Records 
            WHERE patient_id = %s
            ORDER BY record_date DESC
        """, (patient_id,))
        records = cursor.fetchall()

        # Create window for medical report
        report_window = tk.Toplevel(parent_window)
        report_window.title(f"Medical Report - Patient {patient_id}")
        report_window.geometry("1000x700")

        # Patient info
        info_frame = ttk.LabelFrame(report_window, text="Patient Information", padding="20")
        info_frame.pack(fill='x', padx=20, pady=10)

        info_style = {'font': ('Helvetica', 12)}
        ttk.Label(info_frame, text=f"Name: {patient_info[0]}", **info_style).pack(anchor='w')
        ttk.Label(info_frame, text=f"Age: {patient_info[1]}", **info_style).pack(anchor='w')
        ttk.Label(info_frame, text=f"Disease: {patient_info[2]}", **info_style).pack(anchor='w')

        # Records table
        records_frame = ttk.LabelFrame(report_window, text="Medical Records History", padding="20")
        records_frame.pack(fill='both', expand=True, padx=20, pady=10)

        tree = ttk.Treeview(records_frame, columns=("Date", "Diagnosis", "Prescription"), show="headings", height=15)
        tree.heading("Date", text="Date")
        tree.heading("Diagnosis", text="Diagnosis")
        tree.heading("Prescription", text="Prescription")
        tree.column("Date", width=150, anchor='center')
        tree.column("Diagnosis", width=300, anchor='w')
        tree.column("Prescription", width=400, anchor='w')

        y_scrollbar = ttk.Scrollbar(records_frame, orient="vertical", command=tree.yview)
        x_scrollbar = ttk.Scrollbar(records_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)

        tree.pack(side="left", fill="both", expand=True)
        y_scrollbar.pack(side="right", fill="y")
        x_scrollbar.pack(side="bottom", fill="x")

        if records:
            for record in records:
                tree.insert("", "end", values=(record[2], record[1] if record[1] else "N/A", record[0] if record[0] else "N/A"))
        else:
            tree.insert("", "end", values=("N/A", "No Diagnosis Found", "No Prescription Found"))

        # Close button
        ttk.Button(report_window, text="Close", command=report_window.destroy).pack(pady=20)

    finally:
        cursor.close()
        conn.close()

  


def urgent_help(doctor_window):
    kit.sendwhatmsg_instantly(Phone_Number, "There is Emergency..! Need Urgent Help.....!")
    speech("Urgent Help triggered! Contacting emergency team.")



# Function to listen for voice commands
# Global mic status label
mic_status = None  # Declare globally

def listen_for_command(prompt, options, mic_status_label):
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        def update_status(text, color):
            root.after(0, lambda: mic_status_label.config(text=text, fg=color))  # Ensures UI updates in main thread

        update_status("🎤 Listening...", "red")  # Indicate listening status

        try:
            speech(prompt)
            time.sleep(1)
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)

            update_status("Processing...", "blue")  # Update status to processing

            command = recognizer.recognize_google(audio).lower()
            logging.info(f"User said: {command}")

            for option, action in options.items():
                if any(word in command for word in option.split()):  # Partial match

                    speech(f"{action[0]} selected.")
                    action[1]()  # Execute selected action

                    update_status("Idle", "black")  # Reset status after processing

                    # Restart listening in a new thread with the correct mic_status_label
                    threading.Thread(target=listen_for_command, args=(prompt, options, mic_status_label), daemon=True).start()
                    return  # Exit after executing the command

            speech("Command not recognized. Please try again.")

        except sr.UnknownValueError:
            speech("I didn't catch that. Please try again.")
        except sr.RequestError:
            speech("Speech recognition service error.")

        update_status("Idle", "black")  # Reset status if no valid command
        # Restart listening with the correct mic_status_label
        threading.Thread(target=listen_for_command, args=(prompt, options, mic_status_label), daemon=True).start()

button_width = 40  # Fixed width
button_height = 5  # Fixed height


def check_if_doctor(user_id):
    conn = connect_database()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, name FROM Doctors WHERE id = %s", (user_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

# Doctor Mode
def doctor_mode():
    doctor_window = tk.Toplevel(root)
    doctor_window.title("Doctor Dashboard")
    doctor_window.attributes('-fullscreen', True)
    
    set_fullscreen_background(doctor_window, "doctor.jpg")

    font_size = max(18, doctor_window.winfo_screenwidth() // 60)

    label = tk.Label(doctor_window, text="Doctor Dashboard", font=("Arial", font_size, "bold"), fg="blue", bg="white")
    label.pack(pady=20)
    # Restart gesture control thread
    threading.Thread(target=gesture_control, daemon=True).start()

    # Mic Status Label inside Doctor Mode
    doctor_mic_status = tk.Label(doctor_window, text="Idle", font=("Arial", 16, "bold"), fg="black", bg="white")
    doctor_mic_status.pack(pady=10)

    buttons = [
        ("View Patient Records", lambda: view_patient_records(doctor_window)),  # Removed doctor_window argument
        ("Prescribe Medicine", lambda: prescribe_medicine(doctor_window)),
        ("Schedule Appointments", lambda: schedule_appointment(doctor_window)),
        ("Analyze Medical Reports", lambda: analyze_medical_reports(doctor_window)),
        ("Urgent Help", lambda: urgent_help(doctor_window))
    ]
    
    for text, command in buttons:
        btn = ttk.Button(doctor_window, text=text, command=command, width=40)
        btn.pack(pady=10)

    ttk.Button(doctor_window, text="Exit", command=lambda: return_to_main_ui(doctor_window)).pack(pady=10)

    options = {
    "view patient records": ("Viewing Patient Records", lambda: view_patient_records(doctor_window)),
    "patient records": ("Viewing Patient Records", lambda: view_patient_records(doctor_window)),  # Alternative

    "prescribe medicine": ("Prescribing Medicine", lambda: prescribe_medicine(doctor_window)),
    "medicine": ("Prescribing Medicine", lambda: prescribe_medicine(doctor_window)),  # Alternative
    "prescription": ("Prescribing Medicine", lambda: prescribe_medicine(doctor_window)),  # Alternative

    "schedule appointment": ("Scheduling Appointments", lambda: schedule_appointment(doctor_window)),
    "appointment": ("Scheduling Appointments", lambda: schedule_appointment(doctor_window)),  # Alternative
    "set appointment": ("Scheduling Appointments", lambda: schedule_appointment(doctor_window)),  # Alternative

    "analyze reports": ("Analyzing Medical Reports", lambda: analyze_medical_reports(doctor_window)),
    "medical reports": ("Analyzing Medical Reports",lambda: analyze_medical_reports(doctor_window)),  # Alternative
    "analysis": ("Analyzing Medical Reports", lambda:analyze_medical_reports(doctor_window)),  # Alternative

    "Urgent": ("Handling Urgent Help",lambda: urgent_help(doctor_window)),
    "help": ("Handling Urgent Help",lambda: urgent_help(doctor_window)),  # Alternative
    "alert": ("Handling Urgent Help",lambda: urgent_help(doctor_window)),  # Alternative

    "exit": ("Exiting Doctor Mode", lambda: return_to_main_ui(doctor_window))
    }



    threading.Thread(target=listen_for_command, args=("Select an option: View Patient Records, Prescribe Medicine, Schedule Appointments, Analyze Reports, Urgent Help, or Exit.", options, doctor_mic_status), daemon=True).start()

    doctor_window.protocol("WM_DELETE_WINDOW", lambda: return_to_main_ui(doctor_window))

def display_patient_info(user_id):
    patient, doctor = get_patient_records(user_id)
    if patient:
        display_patient_data(patient, doctor)
    else:
        messagebox.showinfo("Error", "No data found for this patient.")

# Show discharge date in a small Tkinter window
def check_discharge_date(user_id):
    conn = connect_database()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT name, discharge_date FROM Patients WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        
        discharge_window = tk.Toplevel()
        discharge_window.title("Discharge Date")
        discharge_window.geometry("400x400")
        discharge_window.resizable(False, False)

        frame = ttk.Frame(discharge_window, padding=20)
        frame.pack(expand=True)

        if result:
            name, discharge_date = result
            name = result[0].strip()

            if discharge_date:
                message = f"{name}, your discharge date is\n{discharge_date}."
            else:
                message = f"{name}, your discharge date\nis not yet set."
        else:
            message = "Patient record not found."

        # label = tk.Label(frame, text=message, font=("Helvetica", 14), justify="center")
        label = tk.Label(
            frame,
            text=message,
            font=("Helvetica", 14),
            justify="center",
            wraplength=350,
            anchor="center"
        )
        label.pack(pady=20)
        

        ttk.Button(frame, text="Close", command=discharge_window.destroy).pack(pady=10)

        speech(message.replace("\n", ". "))

    finally:
        cursor.close()
        conn.close()


# Patient Mode
def patient_mode(user_id=None):
    if user_id is None:
        messagebox.showerror("Error", "Access denied: Face not recognized.")
        return

    patient_window = tk.Toplevel(root)
    patient_window.title("Patient Dashboard")
    patient_window.attributes('-fullscreen', True)

    set_fullscreen_background(patient_window, "patient.jpg")

    font_size = max(18, patient_window.winfo_screenwidth() // 60)

    label = tk.Label(patient_window, text="Patient Dashboard", font=("Arial", font_size, "bold"), fg="blue", bg="white")
    label.pack(pady=20)

    # Mic Status Label inside Patient Mode
    patient_mic_status = tk.Label(patient_window, text="Idle", font=("Arial", 16, "bold"), fg="black", bg="white")
    patient_mic_status.pack(pady=10)
    # Restart gesture control thread
    threading.Thread(target=gesture_control, daemon=True).start()

    buttons = [
        # ("Call Family", lambda: print("Calling Family")),
        ("Urgent Help", lambda: kit.sendwhatmsg_instantly(Phone_Number, "There is Emergency..! Need Urgent Help.....!")),
        ("Entertainment", lambda: entertainment_options(patient_window,user_id)),
        ("View Discharge Date", lambda: check_discharge_date(user_id)),
        ("View Personal Information", lambda: display_patient_info(user_id))
    ]
    
    for text, command in buttons:
        btn = ttk.Button(patient_window, text=text, command=command, width=40)
        btn.pack(pady=10)

    ttk.Button(patient_window, text="Exit", command=lambda: return_to_main_ui(patient_window)).pack(pady=10)

    options = {
        # "call family": ("Calling Family", lambda: print("Calling Family")),
        "urgent help": ("Requesting Urgent Help", lambda: kit.sendwhatmsg_instantly(Phone_Number, "There is Emergency..! Need Urgent Help.....!")),
        "entertainment": ("Opening Entertainment", lambda: entertainment_options(patient_window,user_id)),
        "discharge date": ("Checking Discharge Date", lambda: check_discharge_date(user_id)),
        "personal information": ("Viewing Personal Information", lambda: display_patient_info(user_id)),
        "exit": ("Exiting Patient Mode", lambda: return_to_main_ui(patient_window,user_id))
    }

    threading.Thread(target=listen_for_command, args=("Select an option: Request Urgent Help, Entertainment, View Discharge Date, View Personal Information, or Exit.", options, patient_mic_status), daemon=True).start()

    patient_window.protocol("WM_DELETE_WINDOW", lambda: return_to_main_ui(patient_window))

def entertainment_options(patient_window,user_id):
    """ Opens a new window with entertainment choices. """
    entertainment_window = tk.Toplevel(patient_window)
    entertainment_window.title("Entertainment")
    entertainment_window.geometry("400x300")

    tk.Label(entertainment_window, text="Choose an Entertainment Option:", font=("Arial", 14)).pack(pady=20)

    def open_youtube():
        webbrowser.open("https://www.youtube.com")

    def open_netflix():
        webbrowser.open("https://www.netflix.com")

    def voice_command_website():
        speech("Please say the name of the entertainment website you want to visit.")
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            try:
                audio = recognizer.listen(source)
                website = recognizer.recognize_google(audio).lower().replace(" ", "")
                url = f"https://www.{website}.com"
                speech(f"Opening {website}")
                webbrowser.open(url)
            except sr.UnknownValueError:
                speech("Sorry, I could not understand. Please try again.")
            except sr.RequestError:
                speech("Network error. Please check your internet connection.")

    tk.Button(entertainment_window, text="YouTube", font=("Arial", 12), command=open_youtube).pack(pady=5)
    tk.Button(entertainment_window, text="Netflix", font=("Arial", 12), command=open_netflix).pack(pady=5)
    tk.Button(entertainment_window, text="Choose Your Mode of Entertainment", font=("Arial", 12), command=voice_command_website).pack(pady=5)

# Doctor Mode with Face Login
def face_login_doctor_mode():
    def on_success(user_id):
        doctor_info = check_if_doctor(user_id)
        if doctor_info:
            speech(f"Welcome {doctor_info[1]}")
            doctor_mode()
        else:
            speech("Access denied. You are not registered as a doctor.")
            messagebox.showerror("Access Denied", "This user is not registered as a doctor.")

    face_login(callback_on_success=on_success, is_doctor=True)
# Gesture Control Function

def gesture_control():
    logging.info("Gesture Control running in the background.")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not access the webcam.")
        return

    hand_detector = mp.solutions.hands.Hands()
    screen_width, screen_height = pyautogui.size()
    plocx, plocy = 0, 0
    clocx, clocy = 0, 0
    smoothening = 3

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture frame. Exiting...")
            break
        
        frame = cv2.flip(frame, 1)
        frame_height, frame_width, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        output = hand_detector.process(rgb_frame)
        hands = output.multi_hand_landmarks
        
        if hands:
            for hand in hands:
                landmarks = hand.landmark
                thumb_x = int(landmarks[4].x * frame_width)
                thumb_y = int(landmarks[4].y * frame_height)
                index_x = int(landmarks[8].x * frame_width)
                index_y = int(landmarks[8].y * frame_height)

                distance = math.sqrt((thumb_x - index_x) ** 2 + (thumb_y - index_y) ** 2)
                
                if distance < 30:
                    pyautogui.click()
                    pyautogui.sleep(1)

                clocx = (index_x / frame_width) * screen_width
                clocy = (index_y / frame_height) * screen_height
                clocx = plocx + (clocx - plocx) / smoothening
                clocy = plocy + (clocy - plocy) / smoothening
                pyautogui.moveTo(clocx, clocy)
                plocx, plocy = clocx, clocy
        
        # Remove OpenCV window display (No cv2.imshow)
        
        key = cv2.waitKey(1)
        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# Start gesture control in a separate thread
threading.Thread(target=gesture_control, daemon=True).start()

# Function to return to the main UI after exiting a mode
def return_to_main_ui(window):
    window.destroy()
    # Restart gesture control thread
    threading.Thread(target=gesture_control, daemon=True).start()
    options = {
        "doctor": ("Doctor Mode", doctor_mode),
        "patient": ("Patient Mode", patient_mode)
    }

    global mic_status  # Use the global mic_status defined in the main UI
    threading.Thread(target=listen_for_command, args=("Please select a mode: Doctor Mode, Patient Mode.", options, mic_status), daemon=True).start()

def exit_fullscreen(event=None):
    root.attributes('-fullscreen', False)  # Exit fullscreen for main window

# Main GUI Setup
from PIL import Image, ImageTk

def set_fullscreen_background(window, image_path):
    """Function to dynamically resize and set a fullscreen background image."""
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    try:
        bg_image = Image.open(image_path)
        bg_image = bg_image.resize((screen_width, screen_height), Image.LANCZOS)  # Resize dynamically
        bg_photo = ImageTk.PhotoImage(bg_image)

        bg_label = tk.Label(window, image=bg_photo)
        bg_label.image = bg_photo  # Keep reference
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

    except FileNotFoundError:
        logging.error(f"Background image {image_path} not found.")
        bg_label = tk.Label(window, bg="white")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

# Main GUI
root = tk.Tk()
root.title("Hospital Ecosystem")
root.attributes('-fullscreen', True)

# Apply fullscreen background
set_fullscreen_background(root, "hospital.jpg")
mic_status = tk.Label(root, text="Idle", font=("Arial", 16, "bold"), fg="black", bg="SystemButtonFace")
mic_status.pack(pady=10)
face_scan_status = tk.Label(root, text="Idle", font=("Arial", 16, "bold"), fg="black", bg="SystemButtonFace")
face_scan_status.pack(pady=5)

# Exit fullscreen with Esc key
root.bind("<Escape>", exit_fullscreen)

style = ttk.Style()
style.configure("TButton", font=("Arial", 12, "bold"), padding=10, relief="flat", background="#3498db", foreground="black")
style.map("TButton", background=[("active", "#2980b9")])

# Title Labels
title_label = tk.Label(root, text="Hospital Ecosystem", font=("Arial", 40, "bold"), fg="blue", bg="SystemButtonFace")
title_label.pack(pady=30)

subtitle_label = tk.Label(root, text="Welcome to the Hospital Ecosystem", font=("Arial", 28, "bold"), fg="black", bg="SystemButtonFace")
subtitle_label.pack(pady=20)

mode_label = tk.Label(root, text="Select Mode", font=("Arial", 24, "bold"), fg="black", bg="SystemButtonFace")
mode_label.pack(pady=10)

# Button Container


# Doctor & Patient Buttons
# Create a non-stretching frame for buttons
button_frame = tk.Frame(root, bg="SystemButtonFace")
button_frame.pack(pady=30)  # Do not expand

# Doctor & Patient Buttons with fixed width
doctor_button = ttk.Button(button_frame, text="Doctor Mode", command=face_login_doctor_mode, width=15)
doctor_button.pack(side="left", padx=20, pady=15)  # No expansion

#patient_button = ttk.Button(button_frame, text="Patient Mode", command=patient_mode, width=15)
patient_button = ttk.Button(button_frame, text="Patient Mode", command=lambda: face_login(callback_on_success=patient_mode), width=15)
patient_button.pack(side="left", padx=20, pady=15)  # No expansion

# Start voice command thread for mode selection
options = {
    "doctor": ("Doctor Mode", face_login_doctor_mode),
    "patient": ("Patient Mode", lambda: face_login(callback_on_success=patient_mode)),
}


# Start the thread
threading.Thread(target=listen_for_command, args=("Please select a mode: Doctor Mode, Patient Mode.", options, mic_status), daemon=True).start()

root.mainloop()
