import os
import django
import pandas as pd
import logging
from faker import Faker
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from django.db import IntegrityError
from main_app.models import CustomUser, Campus, Course, LearningRecord, Student, Teacher, PaymentRecord, StudentQuery

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
django.setup()

# Create a Faker generator
fake = Faker()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data_processing.log"),
        logging.StreamHandler()
    ]
)

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
        logging.info(f"Dataframe loaded successfully with {len(df)} rows.")
    except Exception as e:
        logging.error(f"Error reading Excel file: {e}")
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
        logging.info("Columns renamed for Chinese data.")

    required_columns = ['Full Name', 'Class', 'Campus', 'Payment', 'Next Payment Date', 'Total Lessons', 'Lessons Taken', 'Remaining Lessons']
    for column in required_columns:
        if column not in df.columns:
            logging.error(f"Missing required column: {column}")
            return None

    fake_data = []
    user_student_pairs = []

    if is_teacher:
        file = open('fake_users.txt', 'w')
        logging.info("Opened file for writing teacher login information.")

    for index, row in df.iterrows():
        try:
            full_name = row['Full Name']
            email = row['Email'] if not is_chinese_data else fake.email()

            if is_teacher:
                password = get_random_string(12)
                hashed_password = make_password(password)
                file.write(f"Email: {email}, Password: {password}\n")
                logging.info(f"Processed teacher {email} - login info written to file.")
            else:
                password = None
                hashed_password = None
                logging.info(f"Processed student {email} - no login info required.")

            campus_name = row['Campus']
            campus, _ = Campus.objects.get_or_create(name=campus_name)
            logging.info(f"Campus retrieved or created: {campus_name}")

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
                logging.info(f"Course retrieved or created: {course_name}")

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
                logging.info(f"User created: {email}")
            except IntegrityError:
                logging.error(f"IntegrityError for user: {email}")
                continue

            if is_teacher:
                Teacher.objects.get_or_create(user=user)
                logging.info(f"Teacher profile created for: {email}")
            else:
                student, created = Student.objects.get_or_create(
                    admin=user,
                    defaults={
                        'campus': campus,
                        'course': course
                    }
                )
                if not created:
                    student.campus = campus
                    student.course = course
                    student.save()
                    logging.info(f"Updated student {student} with new campus and course.")
                else:
                    logging.info(f"Student created: {student}")

                user_student_pairs.append((user, student, course, row))

        except KeyError as e:
            logging.error(f"KeyError: {e}")
            continue
        except Exception as e:
            logging.error(f"Exception: {e}")
            continue

    if is_teacher:
        file.close()
        logging.info("Teacher login file closed.")

    logging.info("User-student pairs processed: %s", user_student_pairs)

    for user, student, course, row in user_student_pairs:
        try:
            remark = user.remark if student and student.admin else None
            lesson_unit_price = row.get('Lesson Unit Price', 0)
            ls, created = LearningRecord.objects.get_or_create(
                student=student,
                course=course,
                defaults={
                    'date': user.date_joined,
                    # 'teacher',
                    
                }
            )
            PaymentRecord.objects.get_or_create(
                student=student,
                course=course,
                defaults={
                    'date': user.date_joined,
                    'next_payment_date': row['Next Payment Date'],
                    'amount_paid': row['Payment'],
                    'payee': row['Full Name'],
                    'status': 'Currently Learning',
                    'lesson_hours': row['Total Lessons'],
                    'lesson_unit_price': lesson_unit_price,
                    'discounted_price': lesson_unit_price,
                    'book_costs': 0,
                    'other_fee': 0,
                    'amount_due': 0,
                    'remark': user.remark,
                }
            )
            
            StudentQuery.objects.get_or_create(
                student_records=student,
                registered_courses=course,
                admin=user,
                defaults={
                    # 'num_of_classes': row['Total Periods'],
                    'paid_class_hours': row['Total Lessons'],
                    'completed_hours': row['Lessons Taken'],
                    'remaining_hours': row['Remaining Lessons'],
                }
            )
            logging.info(f"StudentQuery created for student: {student}")
        except Exception as e:
            logging.error(f"Error creating LearningRecord: {e}")
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

# Example usage
# process_data('path_to_excel_file.xlsx', is_teacher=True, is_chinese_data=True)
