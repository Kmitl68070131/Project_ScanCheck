# นำเข้าไลบรารีที่จำเป็น
import sqlite3  # สำหรับจัดการฐานข้อมูล SQLite
from datetime import datetime, timedelta  # สำหรับจัดการวันที่และเวลา

class AttendanceDB:
    """คลาสสำหรับจัดการฐานข้อมูลการเข้าเรียน"""
    
    def __init__(self):
        """
        สร้างการเชื่อมต่อกับฐานข้อมูล
        - เชื่อมต่อกับไฟล์ attendance.db
        - อนุญาตให้ใช้งานจากหลาย thread
        """
        self.conn = sqlite3.connect('attendance.db', check_same_thread=False)
        self.init_db()
    
    def init_db(self):
        """
        สร้างตารางในฐานข้อมูลถ้ายังไม่มี
        - ตาราง students เก็บข้อมูลนักศึกษา
        - ตาราง attendance เก็บประวัติการเข้าเรียน
        """
        c = self.conn.cursor()
        # Create students table
        c.execute('''CREATE TABLE IF NOT EXISTS students
                     (student_id TEXT PRIMARY KEY, 
                      name TEXT, 
                      register_date DATE)''')
        # Create attendance table
        c.execute('''CREATE TABLE IF NOT EXISTS attendance
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      student_id TEXT,
                      date DATE,
                      time TIME,
                      FOREIGN KEY(student_id) REFERENCES students(student_id))''')
        self.conn.commit()

    def get_all_students(self):
        """
        ดึงข้อมูลนักศึกษาทั้งหมด
        - คืนค่าเป็น list ของ dict ที่มีข้อมูล id, name, register_date
        """
        c = self.conn.cursor()
        c.execute('SELECT student_id, name, register_date FROM students')
        rows = c.fetchall()
        return [{'id': r[0], 'name': r[1], 'register_date': r[2]} for r in rows]

    def get_recent_attendance(self, days=7):
        """
        ดึงข้อมูลการเข้าเรียนย้อนหลัง N วัน
        - รับพารามิเตอร์ days สำหรับกำหนดจำนวนวันย้อนหลัง
        - เชื่อมข้อมูลระหว่างตาราง attendance และ students
        - เรียงลำดับตามวันที่และเวลาล่าสุด
        """
        c = self.conn.cursor()
        start_date = (datetime.now() - timedelta(days=days)).date()
        c.execute('''
            SELECT a.date, a.time, a.student_id, s.name
            FROM attendance a
            JOIN students s ON a.student_id = s.student_id
            WHERE a.date >= ?
            ORDER BY a.date DESC, a.time DESC
        ''', (start_date,))
        rows = c.fetchall()
        return [{'date': r[0], 'time': r[1], 'student_id': r[2], 'name': r[3]} for r in rows]

    def record_attendance(self, student_id):
        """
        บันทึกการเข้าเรียนของนักศึกษา
        - บันทึกวันที่และเวลาปัจจุบัน
        - คืนค่า True ถ้าสำเร็จ, False ถ้าเกิดข้อผิดพลาด
        """
        try:
            current_date = datetime.now().date()
            current_time = datetime.now().time()
            self.conn.execute('''INSERT INTO attendance (student_id, date, time)
                               VALUES (?, ?, ?)''',
                            (student_id, current_date, current_time))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error recording attendance: {e}")
            return False

    def delete_all_attendance(self):
        """
        ลบข้อมูลการเข้าเรียนทั้งหมด
        - ล้างข้อมูลในตาราง attendance
        - คืนค่า True ถ้าสำเร็จ, False ถ้าเกิดข้อผิดพลาด
        """
        try:
            self.conn.execute("DELETE FROM attendance")
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting attendance: {e}")
            return False
    
    def get_all_records(self):
        """
        ดึงข้อมูลการเข้าเรียนทั้งหมดพร้อมข้อมูลนักศึกษา
        - เชื่อมข้อมูลระหว่างตาราง students และ attendance
        - คำนวณวันในสัปดาห์
        - เรียงตามวันที่และเวลาล่าสุด
        """
        c = self.conn.cursor()
        c.execute('''
            SELECT 
                s.student_id,
                s.name,
                a.date,
                a.first_time,
                strftime('%w', a.date) as weekday
            FROM students s
            LEFT JOIN attendance a ON s.student_id = a.student_id
            ORDER BY a.date DESC, a.first_time DESC
        ''')
        return c.fetchall()

    def search_attendance(self, student_id=None, start_date=None, end_date=None):
        """
        ค้นหาข้อมูลการเข้าเรียนตามเงื่อนไข
        - กรองตาม student_id (ถ้ามี)
        - กรองตามช่วงวันที่ start_date ถึง end_date (ถ้ามี)
        - เรียงลำดับตามวันที่และเวลาล่าสุด
        - คืนค่าเป็น list ของ dict ที่มีข้อมูลการเข้าเรียน
        """
        query = """
            SELECT a.date, a.time, a.student_id, s.name
            FROM attendance a
            LEFT JOIN students s ON a.student_id = s.id
            WHERE 1=1
        """
        params = []
        
        if student_id:
            query += " AND a.student_id = ?"
            params.append(student_id)
        if start_date:
            query += " AND a.date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND a.date <= ?"
            params.append(end_date)
        
        query += " ORDER BY a.date DESC, a.time DESC"
        
        cursor = self.conn.execute(query, params)
        results = cursor.fetchall()
        
        return [{
            'date': row[0],
            'time': row[1],
            'student_id': row[2],
            'name': row[3] if row[3] else 'Unknown'
        } for row in results]
