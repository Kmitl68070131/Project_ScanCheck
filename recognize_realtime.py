# Import libraries ที่จำเป็น
import cv2  # สำหรับการประมวลผลภาพ
import pickle  # สำหรับบันทึกและโหลดข้อมูล
import sqlite3  # สำหรับจัดการฐานข้อมูล
from datetime import datetime  # สำหรับจัดการวันที่และเวลา
import numpy as np  # สำหรับการคำนวณทางคณิตศาสตร์
import os  # สำหรับจัดการไฟล์และโฟลเดอร์

def init_database():
    """
    สร้างและเชื่อมต่อฐานข้อมูล SQLite
    - สร้างตาราง attendance ถ้ายังไม่มี
    - เก็บข้อมูล student_id, date, time
    """
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS attendance
                 (student_id TEXT, date DATE, time TIME)''')
    conn.commit()
    return conn

def record_attendance(conn, student_id):
    """
    บันทึกการเข้าเรียนลงในฐานข้อมูล
    - ตรวจสอบว่าได้บันทึกไปแล้วหรือยังในวันนี้
    - บันทึกเวลาที่เช็คชื่อ
    """
    current_date = datetime.now().date()
    current_time = datetime.now().strftime('%H:%M:%S')  # แปลงเวลาเป็น string
    
    # Check if already recorded today
    c = conn.cursor()
    c.execute('''SELECT * FROM attendance 
                 WHERE student_id = ? AND date = ?''', 
              (student_id, current_date))
    
    if not c.fetchone():
        c.execute('''INSERT INTO attendance (student_id, date, time)
                     VALUES (?, ?, ?)''', 
                  (student_id, current_date, current_time))
        conn.commit()
        print(f"Recorded attendance for {student_id}")

def load_known_faces(dataset_path):
    """
    โหลดและเทรนโมเดลจากรูปภาพในโฟลเดอร์ dataset
    - สร้าง LBPH Face Recognizer
    - โหลดรูปภาพแต่ละคนและตรวจจับใบหน้า
    - สร้าง mapping ระหว่าง ID กับ index
    - เทรนโมเดลและบันทึกไฟล์
    """
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    faces = []
    ids = []
    id_mapping = {}
    
    print("Loading dataset...")
    # เก็บรายการ ID ทั้งหมดก่อน
    all_person_ids = sorted(os.listdir(dataset_path))
    
    # สร้าง mapping โดยใช้ index เป็นลำดับตามตัวอักษร
    for idx, person_id in enumerate(all_person_ids):
        id_mapping[person_id] = idx
    
    for person_id in all_person_ids:
        person_dir = os.path.join(dataset_path, person_id)
        if os.path.isdir(person_dir):
            print(f"Processing ID: {person_id}")
            face_count = 0
            for image_file in os.listdir(person_dir):
                image_path = os.path.join(person_dir, image_file)
                img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    face_rect = face_cascade.detectMultiScale(img)
                    for (x, y, w, h) in face_rect:
                        faces.append(cv2.equalizeHist(img[y:y+h, x:x+w]))
                        ids.append(id_mapping[person_id])
                        face_count += 1
            print(f"Found {face_count} faces for ID {person_id}")
    
    if not faces:
        raise ValueError("No faces found in dataset")
    
    print(f"Training model with {len(faces)} faces...")
    recognizer.train(faces, np.array(ids))
    
    # Save model and mapping
    model_path = "face_model.yml"
    mapping_path = "id_mapping.pickle"
    
    recognizer.save(model_path)
    with open(mapping_path, "wb") as f:
        # บันทึก mapping แบบสองทาง
        mapping_data = {
            'id_to_num': id_mapping,
            'num_to_id': {v: k for k, v in id_mapping.items()}
        }
        pickle.dump(mapping_data, f)
    
    print("Model trained and saved successfully")
    return recognizer

def check_face_quality(face_img):
    """
    ตรวจสอบคุณภาพของภาพใบหน้า
    - ตรวจสอบความชัดของภาพด้วย Laplacian
    - ตรวจสอบความสว่างของภาพ
    - คืนค่า True ถ้าผ่านเกณฑ์
    """
    # ตรวจสอบความชัดของภาพ
    laplacian_var = cv2.Laplacian(face_img, cv2.CV_64F).var()
    # ตรวจสอบความสว่าง
    brightness = face_img.mean()
    return laplacian_var > 100 and 50 < brightness < 200

def enhance_face_image(face_img):
    """
    ปรับปรุงคุณภาพของภาพใบหน้า
    - ปรับความคมชัดด้วย CLAHE
    - ลดสัญญาณรบกวนด้วย Non-local Means Denoising
    - คืนค่าภาพที่ปรับปรุงแล้ว
    """
    # ปรับความคมชัด
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(face_img)
    # ลดนอยส์
    denoised = cv2.fastNlMeansDenoising(enhanced)
    return denoised

def recognize_faces():
    """
    ฟังก์ชันหลักสำหรับการรู้จำใบหน้าแบบ Real-time
    - โหลดหรือเทรนโมเดลใหม่
    - เปิดกล้องและเริ่มการตรวจจับใบหน้า
    - ทำการรู้จำใบหน้าและแสดงผล
    - บันทึกการเข้าเรียนเมื่อตรวจจับได้
    """
    # Load face detector and recognizer
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    
    # Load or train model
    dataset_path = "dataset"
    need_training = not os.path.exists("face_model.yml") or not os.path.exists("id_mapping.pickle")
    
    if need_training:
        print("Training new face model...")
        if not os.path.exists(dataset_path):
            print(f"Error: Dataset directory '{dataset_path}' not found")
            return
        if not os.listdir(dataset_path):
            print(f"Error: Dataset directory '{dataset_path}' is empty")
            return
        try:
            recognizer = load_known_faces(dataset_path)
            print("Model training completed successfully")
        except Exception as e:
            print(f"Error during model training: {str(e)}")
            return
    else:
        try:
            recognizer.read("face_model.yml")
            print("Existing model loaded successfully")
        except Exception as e:
            print(f"Error loading face model: {str(e)}")
            print("Attempting to retrain model...")
            recognizer = load_known_faces(dataset_path)
    
    # Load ID mapping
    try:
        with open("id_mapping.pickle", "rb") as f:
            mapping_data = pickle.load(f)
            num_to_id = mapping_data['num_to_id']
    except FileNotFoundError:
        print("Error: id_mapping.pickle not found. Please retrain the model.")
        return
    except Exception as e:
        print(f"Error loading ID mapping: {str(e)}")
        return

    # Initialize variables
    confidence_threshold = 65
    min_neighbors = 5
    recognition_history = []  # เก็บประวัติการรู้จำ
    history_size = 5  # จำนวนเฟรมที่ใช้ในการยืนยัน
    
    conn = init_database()
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    
    print(f"Recognition started. Confidence threshold: {confidence_threshold}")
    print("Press 'q' to quit, '+'/'-' to adjust threshold")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # ปรับปรุงคุณภาพภาพ
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        
        # ตรวจจับใบหน้า
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=min_neighbors,
            minSize=(60, 60),  # เพิ่มขนาดขั้นต่ำ
            maxSize=(300, 300)  # จำกัดขนาดสูงสุด
        )
        
        for (x, y, w, h) in faces:
            face_roi = gray[y:y+h, x:x+w]
            
            # ตรวจสอบคุณภาพใบหน้า
            if not check_face_quality(face_roi):
                continue
                
            # ปรับปรุงคุณภาพภาพใบหน้า
            face = enhance_face_image(cv2.resize(face_roi, (200, 200)))
            
            try:
                # ทำการรู้จำใบหน้า
                label, confidence = recognizer.predict(face)
                
                if confidence < confidence_threshold:
                    student_id = num_to_id.get(label, "Unknown")
                    
                    # เพิ่มผลการรู้จำลงในประวัติ
                    recognition_history.append((student_id, confidence))
                    if len(recognition_history) > history_size:
                        recognition_history.pop(0)
                    
                    # ตรวจสอบความสอดคล้อง
                    if len(recognition_history) >= 3:
                        recent_ids = [r[0] for r in recognition_history[-3:]]
                        if all(id == student_id for id in recent_ids):
                            record_attendance(conn, student_id)
                            color = (0, 255, 0)
                            text = f"ID: {student_id} ({confidence:.1f})"
                        else:
                            color = (0, 255, 255)
                            text = "Verifying..."
                    else:
                        color = (0, 255, 255)
                        text = "Verifying..."
                else:
                    color = (0, 0, 255)
                    text = f"Unknown ({confidence:.1f})"
                
                # แสดงผล
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                cv2.putText(frame, text, (x, y-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                
                # แสดงค่าคุณภาพภาพ
                quality_text = f"Quality: {check_face_quality(face_roi)}"
                cv2.putText(frame, quality_text, (x, y+h+20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                
            except Exception as e:
                print(f"Error during recognition: {str(e)}")
        
        cv2.imshow('Face Recognition', frame)
        
        # Handle key events
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('+') and confidence_threshold < 100:
            confidence_threshold += 5
            print(f"Confidence threshold: {confidence_threshold}")
        elif key == ord('-') and confidence_threshold > 0:
            confidence_threshold -= 5
            print(f"Confidence threshold: {confidence_threshold}")
    
    cap.release()
    cv2.destroyAllWindows()
    conn.close()

def search_attendance_history(student_id=None, date=None):
    """
    ค้นหาประวัติการเข้าเรียน
    - ค้นหาตาม student_id และ/หรือ วันที่
    - เรียงลำดับตามวันที่และเวลาล่าสุด
    """
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    
    query = "SELECT student_id, date, time FROM attendance WHERE 1=1"
    params = []
    
    if student_id:
        query += " AND student_id = ?"
        params.append(student_id)
    if date:
        query += " AND date = ?"
        params.append(date)
    
    query += " ORDER BY date DESC, time DESC"
    
    c.execute(query, params)
    results = c.fetchall()
    conn.close()
    return results

def display_attendance_menu():
    """
    แสดงเมนูสำหรับการค้นหาประวัติการเข้าเรียน
    - ค้นหาตาม ID
    - ค้นหาตามวันที่
    - แสดงทั้งหมด
    """
    while True:
        print("\nAttendance History Search")
        print("1. Search by Student ID")
        print("2. Search by Date")
        print("3. Show All Records")
        print("4. Return to Main Menu")
        
        choice = input("Enter your choice (1-4): ")
        
        if choice == '1':
            student_id = input("Enter Student ID: ")
            results = search_attendance_history(student_id=student_id)
        elif choice == '2':
            date_str = input("Enter Date (YYYY-MM-DD): ")
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
                results = search_attendance_history(date=date)
            except ValueError:
                print("Invalid date format! Please use YYYY-MM-DD")
                continue
        elif choice == '3':
            results = search_attendance_history()
        elif choice == '4':
            break
        else:
            print("Invalid choice!")
            continue
        
        if results:
            print("\nAttendance Records:")
            print("Student ID\tDate\t\tTime")
            print("-" * 40)
            for record in results:
                print(f"{record[0]}\t\t{record[1]}\t{record[2]}")
        else:
            print("No records found!")

def main():
    """
    ฟังก์ชันหลักของโปรแกรม
    - แสดงเมนูหลัก
    - จัดการการทำงานของระบบ
    """
    while True:
        print("\nFace Recognition Attendance System")
        print("1. Start Recognition")
        print("2. Search Attendance History")
        print("3. Exit")
        
        choice = input("Enter your choice (1-3): ")
        
        if choice == '1':
            recognize_faces()
        elif choice == '2':
            display_attendance_menu()
        elif choice == '3':
            print("Goodbye!")
            break
        else:
            print("Invalid choice!")

if __name__ == "__main__":
    main()
    main()
