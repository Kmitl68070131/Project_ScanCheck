import cv2
import os
import sqlite3
from datetime import datetime

def init_database():
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS students
                 (student_id TEXT PRIMARY KEY, name TEXT, register_date DATE)''')
    conn.commit()
    return conn

def create_dataset_folder(student_id):
    """Create folder for student images if not exists"""
    path = f"dataset/{student_id}"
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def capture_faces():
    conn = init_database()
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
        
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # Get student info
    while True:
        student_id = input("Enter student ID: ").strip()
        if not student_id:
            print("Error: Student ID cannot be empty")
            continue
            
        # Check if student ID exists
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM students WHERE student_id = ?", (student_id,))
        existing_student = cursor.fetchone()
        
        if existing_student:
            print(f"Student ID {student_id} already exists with name: {existing_student[0]}")
            choice = input("Do you want to update this student's data? (y/n): ").lower()
            if choice == 'y':
                name = input("Enter new student name: ").strip()
                if not name:
                    print("Error: Name cannot be empty")
                    continue
                    
                # Update existing student
                conn.execute("UPDATE students SET name = ?, register_date = ? WHERE student_id = ?",
                           (name, datetime.now().date(), student_id))
                conn.commit()
                
                # Delete existing face images
                dataset_path = f"dataset/{student_id}"
                if os.path.exists(dataset_path):
                    for file in os.listdir(dataset_path):
                        os.remove(os.path.join(dataset_path, file))
                break
            else:
                continue
        else:
            name = input("Enter student name: ").strip()
            if not name:
                print("Error: Name cannot be empty")
                continue
                
            # Insert new student
            conn.execute("INSERT INTO students (student_id, name, register_date) VALUES (?, ?, ?)",
                        (student_id, name, datetime.now().date()))
            conn.commit()
            break

    dataset_path = create_dataset_folder(student_id)
    print(f"Press 'c' to capture face (20 remaining)")
    print("Press 'q' to quit")
    
    count = 0
    while count < 20:  # Changed from 10 to 20
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame")
            break
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        # Draw rectangle and text
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            cv2.putText(frame, f"Face detected! Press 'c' to capture", (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
            
        cv2.imshow('Capturing Face', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('c'):
            if len(faces) > 0:
                x, y, w, h = faces[0]  # Get first detected face
                
                # เพิ่มขอบรอบใบหน้า 50%
                margin_x = int(w * 0.5)
                margin_y = int(h * 0.5)
                
                # คำนวณพื้นที่ใหม่โดยเพิ่มขอบ
                x1 = max(0, x - margin_x)
                y1 = max(0, y - margin_y)
                x2 = min(frame.shape[1], x + w + margin_x)
                y2 = min(frame.shape[0], y + h + margin_y)
                
                # ตัดภาพใบหน้าพร้อมขอบ
                face_img = frame[y1:y2, x1:x2]
                
                # บันทึกภาพ
                img_path = os.path.join(dataset_path, f"{student_id}_{count}.jpg")
                
                if cv2.imwrite(img_path, face_img):
                    print(f"Captured image {count+1}/20 - Saved to {img_path}")  # Changed from 10 to 20
                    count += 1
                    if count < 20:  # Changed from 10 to 20
                        print(f"Press 'c' to capture ({20-count} remaining)")  # Changed from 10 to 20
                else:
                    print("Error: Could not save image")
            else:
                print("No face detected! Please try again")
                
        elif key == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    if count == 20:  # Changed from 10 to 20
        print("Successfully captured all 20 images!")  # Changed from 10 to 20
    else:
        print(f"Captured {count} images before exiting")

if __name__ == "__main__":
    if not os.path.exists("dataset"):
        os.makedirs("dataset")
    capture_faces()
