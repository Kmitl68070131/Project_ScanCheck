import cv2  # ไลบรารีสำหรับการประมวลผลภาพ
import numpy as np  # ไลบรารีสำหรับการคำนวณทางคณิตศาสตร์
import pickle  # ไลบรารีสำหรับการบันทึกและโหลดข้อมูล
import os  # ไลบรารีสำหรับจัดการไฟล์และโฟลเดอร์

def encode_faces():
    """
    ฟังก์ชันสำหรับสร้างรหัสใบหน้าจากรูปภาพในโฟลเดอร์ dataset
    - สร้าง face encodings สำหรับทุกรูปภาพ
    - จัดการการแปลงข้อมูลใบหน้าเป็นรหัสที่ใช้ในการจดจำ
    """
    # ตัวแปรสำหรับเก็บข้อมูลใบหน้าและชื่อ
    known_faces = []  # เก็บข้อมูลใบหน้าที่รู้จัก
    known_names = []  # เก็บชื่อที่สอดคล้องกับใบหน้า
    label_ids = {}    # dictionary เก็บการจับคู่ระหว่าง ID กับ label
    current_label = 0 # ตัวนับสำหรับกำหนด label
    
    # โหลดโมเดลสำหรับตรวจจับใบหน้า
    face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # สร้าง recognizer สำหรับการจดจำใบหน้า
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    
    # วนลูปผ่านแต่ละโฟลเดอร์ของแต่ละคน
    for person_id in os.listdir("dataset"):
        person_dir = os.path.join("dataset", person_id)
        if os.path.isdir(person_dir):
            # กำหนด label ให้กับแต่ละคน
            if person_id not in label_ids:
                label_ids[person_id] = current_label
                current_label += 1
                
            faces = []   # เก็บใบหน้าของคนนี้
            labels = []  # เก็บ label ของคนนี้
            
            # ประมวลผลแต่ละรูปภาพ
            for image_name in os.listdir(person_dir):
                image_path = os.path.join(person_dir, image_name)
                
                try:
                    # อ่านรูปภาพและแปลงเป็นโทนสีเทา
                    image = cv2.imread(image_path)
                    if image is None:
                        print(f"Could not read {image_path}")
                        continue
                        
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    detected_faces = face_detector.detectMultiScale(gray, 1.3, 5)
                    
                    # ถ้าพบใบหน้า
                    if len(detected_faces) > 0:
                        (x, y, w, h) = detected_faces[0]
                        # ตัดเฉพาะส่วนใบหน้าและปรับขนาด
                        face_img = cv2.resize(gray[y:y+h, x:x+w], (200, 200))
                        faces.append(face_img)
                        labels.append(label_ids[person_id])
                        print(f"Processed {image_path}")
                    else:
                        print(f"No face found in {image_path}")
                except Exception as e:
                    print(f"Error processing {image_path}: {str(e)}")
            
            # ถ้ามีใบหน้าที่พบ
            if faces:
                known_faces.extend(faces)
                known_names.extend([person_id] * len(faces))
    
    # ถ้ามีข้อมูลใบหน้าและชื่อ
    if known_faces and known_names:
        try:
            # แปลงลิสต์เป็น numpy array
            faces_array = np.array(known_faces)
            labels_array = np.array(labels)
            
            # เทรนโมเดล recognizer
            recognizer.train(faces_array, labels_array)
            
            # บันทึกโมเดล
            recognizer.write("face_model.yml")
            
            # บันทึกข้อมูล mapping ระหว่างชื่อและ label
            data = {
                "names": known_names,
                "label_ids": label_ids
            }
            with open("encodings.pickle", "wb") as f:
                pickle.dump(data, f)
            
            print("Encoding completed and saved successfully")
            print(f"Total faces encoded: {len(faces_array)}")
            print(f"Total people: {len(label_ids)}")
        except Exception as e:
            print(f"Error during training: {str(e)}")
    else:
        print("No faces found in dataset!")

if __name__ == "__main__":
    encode_faces()  # เริ่มการทำงานของโปรแกรม
