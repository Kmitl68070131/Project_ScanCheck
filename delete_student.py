import sqlite3
import os
import shutil

def delete_student():
    # เชื่อมต่อฐานข้อมูล
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    
    while True:
        # แสดงรายชื่อนักศึกษาทั้งหมด
        print("\nรายชื่อนักศึกษาที่ลงทะเบียน:")
        print("-" * 50)
        c.execute("SELECT student_id, name FROM students")
        students = c.fetchall()
        
        if not students:
            print("ไม่พบข้อมูลนักศึกษา")
            break
            
        for student in students:
            print(f"รหัส: {student[0]}, ชื่อ: {student[1]}")
        print("-" * 50)
        
        # รับ input รหัสนักศึกษาที่ต้องการลบ
        student_id = input("\nใส่รหัสนักศึกษาที่ต้องการลบ (กด Enter เพื่อออก): ").strip()
        
        if not student_id:
            break
            
        # ตรวจสอบว่ามีรหัสนักศึกษานี้หรือไม่
        c.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
        if not c.fetchone():
            print(f"ไม่พบรหัสนักศึกษา {student_id}")
            continue
            
        confirm = input(f"ยืนยันการลบข้อมูลรหัส {student_id}? (y/n): ").lower()
        if confirm == 'y':
            try:
                # ลบข้อมูลจากตาราง students
                c.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
                # ลบข้อมูลจากตาราง attendance
                c.execute("DELETE FROM attendance WHERE student_id = ?", (student_id,))
                conn.commit()
                
                # ลบโฟลเดอร์รูปภาพ
                student_folder = os.path.join("dataset", student_id)
                if os.path.exists(student_folder):
                    shutil.rmtree(student_folder)
                
                print(f"ลบข้อมูลรหัส {student_id} เรียบร้อยแล้ว")
                
                # ถามว่าต้องการลบข้อมูลคนอื่นต่อหรือไม่
                if input("ต้องการลบข้อมูลคนอื่นต่อหรือไม่? (y/n): ").lower() != 'y':
                    break
            except Exception as e:
                print(f"เกิดข้อผิดพลาด: {str(e)}")
                conn.rollback()
    
    conn.close()
    print("\nปิดโปรแกรม")

if __name__ == "__main__":
    delete_student()
