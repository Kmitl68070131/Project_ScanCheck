import sqlite3
from datetime import datetime, timedelta

class AttendanceDB:
    def __init__(self):
        self.conn = sqlite3.connect('attendance.db', check_same_thread=False)
        self.init_db()
    
    def init_db(self):
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
        """Get all registered students"""
        c = self.conn.cursor()
        c.execute('SELECT student_id, name, register_date FROM students')
        rows = c.fetchall()
        return [{'id': r[0], 'name': r[1], 'register_date': r[2]} for r in rows]

    def get_recent_attendance(self, days=7):
        """Get attendance records for the last N days"""
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
        """Record attendance for a student"""
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
        """Delete all attendance records"""
        try:
            self.conn.execute("DELETE FROM attendance")
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting attendance: {e}")
            return False
    
    def get_all_records(self):
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
        """Search attendance records with filters"""
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
