import os
import django
import pandas as pd
from faker import Faker
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from django.db import IntegrityError
from main_app.models import CustomUser, Campus, Course, LearningRecord, Student, Teacher

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
django.setup()

# Create a Faker generator
fake = Faker()

# Mapping Chinese ordinal numbers to grades
grade_mapping = {
    '一阶': 1,
    '二阶': 2,
    '三阶': 3,
    '四阶': 4
}

def process_data(excel_file, is_teacher, is_chinese_data=False):
    try:
        df = pd.read_excel(excel_file)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None  # Return early if the file cannot be processed

    if is_chinese_data:
        column_mapping = {
            '序号': 'Index',
            '学生姓名': 'Full Name',
            '班级': 'Class',
            '校区': 'Campus',
            '缴费': 'Payment',
            '期别': 'Period',
            '累计报名期次': 'Total Periods',
            '销售人员': 'Salesperson',
            '总课次': 'Total Lessons',
            '已上课次': 'Lessons Taken',
            '剩余课次': 'Remaining Lessons',
            '下次缴费时间\n（课程结束前1月）': 'Next Payment Date',
            '授课老师': 'Teacher'
        }
        df.rename(columns=column_mapping, inplace=True)

    required_columns = ['Full Name', 'Class', 'Campus', 'Payment', 'Next Payment Date', 'Total Lessons', 'Lessons Taken', 'Remaining Lessons']
    for column in required_columns:
        if column not in df.columns:
            print(f"Missing required column: {column}")
            return None

    fake_data = []
    user_student_pairs = []

    if is_teacher:
        file = open('fake_users.txt', 'w')

    for index, row in df.iterrows():
        try:
            full_name = row['Full Name']
            email = row['Email'] if not is_chinese_data else fake.email()

            if is_teacher:
                password = get_random_string(12)
                hashed_password = make_password(password)
                file.write(f"Email: {email}, Password: {password}\n")
            else:
                password = None
                hashed_password = None

            campus_name = row['Campus']
            campus, _ = Campus.objects.get_or_create(name=campus_name)

            class_full_name = row['Class']
            course_name, grade_level = None, None
            for chinese_grade, grade in grade_mapping.items():
                if chinese_grade in class_full_name:
                    course_name = class_full_name.replace(chinese_grade, '').strip()
                    grade_level = grade
                    break

            if course_name:
                course, created = Course.objects.get_or_create(name=course_name)
                if created or course.level_end < grade_level:
                    course.level_end = grade_level
                    course.save()

            user_data = {
                'full_name': full_name,
                'email': email,
                'password': hashed_password,
                'profile_pic': '/media/default.jpg',
                'gender': row['Gender'] if not is_chinese_data else fake.random_element(elements=('男', '女')),
                'address': row['Address'] if not is_chinese_data else fake.address().replace('\n', ', '),
                'phone_number': row['Phone Number'] if not is_chinese_data else fake.phone_number(),
                'is_teacher': is_teacher,
                'user_type': 2 if is_teacher else 3,  
                'remark': "Salesperson: " + row['Salesperson'],
                'fcm_token': ''  
            }

            try:
                user = CustomUser.objects.create_user(**user_data)
                fake_data.append(user_data)
            except IntegrityError:
                print(f"IntegrityError for user: {email}")
                continue

            if is_teacher:
                Teacher.objects.get_or_create(user=user)
            else:
                student, _ = Student.objects.get_or_create(campus=campus, admin=user, course=course)
                user_student_pairs.append((user, student, course, row))
                print(f"Student created: {student}")

        except KeyError as e:
            print(f"KeyError: {e}")
            continue
        except Exception as e:
            print(f"Exception: {e}")
            continue

    if is_teacher:
        file.close()

    # Create learning records for each student
    for user, student, course, row in user_student_pairs:
        try:
            # Get the remark from the associated student admin user
            remark = student.admin.remark if student and student.admin else None

            # Creating the LearningRecord instance
            LearningRecord.objects.get_or_create(
                student=student,
                course=course,
                defaults={
                    'total_lessons': row['Total Lessons'],
                    'lessons_taken': row['Lessons Taken'],
                    'remaining_lessons': row['Remaining Lessons'],
                    'remark': remark  # Assign the remark here
                }
            )
            print(f"LearningRecord created for student: {student}")
        except Exception as e:
            print(f"Error creating LearningRecord: {e}")
            continue

    return fake_data

def generate_html_table(data):
    if not data:
        return "<p>No data available</p>"

    table = "<table border='1'>"
    headers = data[0].keys()
    table += "<tr>" + "".join([f"<th>{header}</th>" for header in headers]) + "</tr>"
    for row in data:
        table += "<tr>" + "".join([f"<td>{value}</td>" for value in row.values()]) + "</tr>"
    table += "</table>"
    return table
