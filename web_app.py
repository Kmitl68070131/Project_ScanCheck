from flask import Flask, render_template_string, redirect, url_for
from database import AttendanceDB
from datetime import datetime
import pandas as pd

app = Flask(__name__)
db = AttendanceDB()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>ระบบเช็คชื่อด้วยใบหน้า</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <h1 class="mb-4">ระบบเช็คชื่อด้วยใบหน้า</h1>
        
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        <h5 class="mb-0">สถิติวันนี้ ({{today_thai}})</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-6">
                                <h6>จำนวนผู้ลงทะเบียน:</h6>
                                <h3>{{total_students}} คน</h3>
                            </div>
                            <div class="col-6">
                                <h6>เข้าเรียนวันนี้:</h6>
                                <h3>{{today_count}} คน</h3>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header bg-info text-white">
                        <h5 class="mb-0">การจัดการ</h5>
                    </div>
                    <div class="card-body">
                        <a href="/clear" class="btn btn-danger" 
                           onclick="return confirm('ยืนยันการลบข้อมูลการเช็คชื่อทั้งหมด?')">
                            ลบข้อมูลการเช็คชื่อทั้งหมด
                        </a>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header bg-success text-white">
                        <h5 class="mb-0">รายชื่อผู้ลงทะเบียน</h5>
                    </div>
                    <div class="card-body">
                        <table class="table table-bordered table-hover">
                            <thead class="table-light">
                                <tr>
                                    <th>รหัสนักศึกษา</th>
                                    <th>ชื่อ-นามสกุล</th>
                                    <th>วันที่ลงทะเบียน</th>
                                    <th>สถานะวันนี้</th>
                                    <th>เวลาเข้าเรียนล่าสุด</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for student in students %}
                                <tr>
                                    <td>{{student.id}}</td>
                                    <td>{{student.name}}</td>
                                    <td>{{student.register_date}}</td>
                                    <td>
                                        {% if student.attended_today %}
                                        <span class="badge bg-success">เข้าเรียนแล้ว</span>
                                        {% else %}
                                        <span class="badge bg-secondary">ยังไม่เข้าเรียน</span>
                                        {% endif %}
                                    </td>
                                    <td>{{student.last_attendance or '-'}}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mt-4">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header bg-warning">
                        <h5 class="mb-0">ประวัติการเช็คชื่อ (7 วันล่าสุด)</h5>
                    </div>
                    <div class="card-body">
                        <table class="table table-bordered table-hover">
                            <thead class="table-light">
                                <tr>
                                    <th>วันที่</th>
                                    <th>เวลา</th>
                                    <th>รหัสนักศึกษา</th>
                                    <th>ชื่อ-นามสกุล</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for record in attendance_records %}
                                <tr>
                                    <td>{{record.date}}</td>
                                    <td>{{record.time}}</td>
                                    <td>{{record.student_id}}</td>
                                    <td>{{record.name}}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script>
        setTimeout(function(){ location.reload(); }, 30000);
    </script>
</body>
</html>
'''

def convert_to_thai_date(date_str):
    thai_months = [
        "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
        "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
    ]
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    return f"{date_obj.day} {thai_months[date_obj.month-1]} {date_obj.year+543}"

@app.route('/')
def index():
    # Get all students
    students = db.get_all_students()
    
    # Get today's attendance
    today = datetime.now().date()
    today_str = today.strftime('%Y-%m-%d')
    attendance_records = db.get_recent_attendance(7)  # Get last 7 days
    
    # Process student data
    student_list = []
    for student in students:
        attended_today = any(
            record['student_id'] == student['id'] and 
            record['date'] == today_str 
            for record in attendance_records
        )
        
        # Get last attendance
        student_records = [r for r in attendance_records if r['student_id'] == student['id']]
        last_attendance = student_records[0]['time'] if student_records else None
        
        student_list.append({
            'id': student['id'],
            'name': student['name'],
            'register_date': convert_to_thai_date(student['register_date']),
            'attended_today': attended_today,
            'last_attendance': last_attendance
        })
    
    today_count = len([s for s in student_list if s['attended_today']])
    
    return render_template_string(
        HTML_TEMPLATE,
        students=student_list,
        attendance_records=attendance_records,
        today_thai=convert_to_thai_date(today_str),
        today_count=today_count,
        total_students=len(students)
    )

@app.route('/clear')
def clear_attendance():
    db.delete_all_attendance()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
