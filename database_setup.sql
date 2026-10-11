-- =======================================================
-- Hospital Ecosystem Database Setup Script
-- Database Name: HospitalDB
-- =======================================================

CREATE DATABASE IF NOT EXISTS HospitalDB;
USE HospitalDB;

-- 1. Doctors Table
CREATE TABLE IF NOT EXISTS Doctors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    specialization VARCHAR(255),
    phone VARCHAR(20),
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Patients Table
CREATE TABLE IF NOT EXISTS Patients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    age INT,
    disease VARCHAR(255),
    doctor_id INT,
    joining_date DATE,
    discharge_date DATE,
    phone VARCHAR(20),
    emergency_contact VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doctor_id) REFERENCES Doctors(id) ON DELETE SET NULL
);

-- 3. Medical Records Table
CREATE TABLE IF NOT EXISTS Records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    diagnosis TEXT,
    prescription TEXT,
    record_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES Patients(id) ON DELETE CASCADE
);

-- 4. Appointments Table
CREATE TABLE IF NOT EXISTS Appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT,
    date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'Scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES Patients(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES Doctors(id) ON DELETE SET NULL
);

-- Sample Data (Optional Seed Data)
INSERT INTO Doctors (id, name, specialization, phone, email) 
VALUES 
    (1, 'Dr. Sarah Connor', 'General Physician', '+1234567890', 'sconnor@hospital.org'),
    (2, 'Dr. Alan Grant', 'Cardiology', '+1234567891', 'agrant@hospital.org')
ON DUPLICATE KEY UPDATE name=VALUES(name);

INSERT INTO Patients (id, name, age, disease, doctor_id, joining_date, discharge_date, phone) 
VALUES 
    (1, 'John Doe', 35, 'Viral Infection', 1, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 5 DAY), '+1234567892'),
    (2, 'Jane Smith', 42, 'Hypertension', 2, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 3 DAY), '+1234567893')
ON DUPLICATE KEY UPDATE name=VALUES(name);

INSERT INTO Records (patient_id, diagnosis, prescription)
VALUES 
    (1, 'Acute viral fever with mild dehydration', 'Paracetamol 650mg TDS, ORS fluids, Multivitamins'),
    (2, 'Stage 1 Essential Hypertension', 'Amlodipine 5mg OD, Low sodium diet, Exercise')
ON DUPLICATE KEY UPDATE diagnosis=VALUES(diagnosis);
