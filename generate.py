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
    format='%(asctime)s - %(LEVELNAME)s - %(MESSAGE)s',
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
            '总课时': 'Total Lesson Hours',
            '已完成课时': 'Completed Lesson Hours',
            '剩余课时': 'Remaining Lesson Hours',
            '课程数量': 'Number of Classes',
            '下次缴费时间\n（课程结束前1月）': 'Next Payment Date',
            '授课老师': 'Teacher',
            '书本费': 'Book Costs',
            '其他费用': 'Other Fee',
            '应付金额': 'Amount Due',
            '支付方式': 'Payment Method',
            '注册日期': 'Enrollment Date',
            '缴费日期': 'Payment Date',
            '性别': 'Gender'
        }
        df.rename(columns=column_mapping, inplace=True)
        logging.info("Columns renamed for Chinese data.")

    required_columns = ['Full Name', 'Class', 'Campus', 'Payment', 'Next Payment Date', 'Total Lesson Hours', 'Completed Lesson Hours', 'Remaining Lesson Hours']
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
            full_name = row.get('Full Name', fake.name())
            email = row.get('Email', fake.email())

            if is_teacher:
                password = get_random_string(12)
                hashed_password = make_password(password)
                file.write(f"Email: {email}, Password: {password}\n")
                logging.info(f"Processed teacher {email} - login info written to file.")
            else:
                password = None
                hashed_password = None
                logging.info(f"Processed student {email} - no login info required.")

            campus_name = row.get('Campus', 'Unknown Campus')
            campus, _ = Campus.objects.get_or_create(name=campus_name)
            logging.info(f"Campus retrieved or created: {campus_name}")

            class_full_name = row.get('Class', 'Unknown Class')
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
                'gender': row.get('Gender', fake.random_element(elements=('男', '女'))),
                'address': row.get('Address', fake.address().replace('\n', ', ')),
                'phone_number': row.get('Phone Number', fake.phone_number()),
                'is_teacher': is_teacher,
                'user_type': 2 if is_teacher else 3,  
                'remark': "Salesperson: " + row.get('Salesperson', 'Unknown'),
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
    
    if not is_teacher:
        for user, student, course, row in user_student_pairs:
            try:
                remark = user.remark if student and student.admin else None
                total_price = row.get('Amount Due', 0)
                total_lesson_hours = row.get('Total Lesson Hours', 0)
                
                if total_lesson_hours > 0:
                    lesson_unit_price = total_price / total_lesson_hours
                else:
                    lesson_unit_price = 2180

                discounted_price = lesson_unit_price * total_lesson_hours

                ls, created = LearningRecord.objects.update_or_create(
                    student=student,
                    course=course,
                    defaults={
                        'date': user.date_joined,
                    }
                )

                ps, created = PaymentRecord.objects.update_or_create(
                    student=student,
                    course=course,
                    defaults={
                        'date': user.date_joined,
                        'next_payment_date': row.get('Next Payment Date', fake.date_this_year()),
                        'amount_paid': row.get('Payment', 0),
                        'payee': row.get('Full Name', 'Unknown'),
                        'status': 'Currently Learning',
                        'lesson_hours': total_lesson_hours,
                        'lesson_unit_price': lesson_unit_price,
                        'discounted_price': discounted_price,
                        'book_costs': row.get('Book Costs', 0),
                        'other_fee': row.get('Other Fee', 0),
                        'amount_due': total_price,
                        'payment_method': row.get('Payment Method', 'Please Update'),
                        'remark': remark,
                        'total_semester': row.get('Total Periods', 1)
                    }
                )

                sq, created = StudentQuery.objects.update_or_create(
                    student_records=student,
                    registered_courses=course,
                    admin=user,
                    learning_records=ls,
                    payment_records=ps,
                    defaults={
                        'num_of_classes': row.get('Number of Classes', 1),
                        'paid_class_hours': total_lesson_hours,
                        'completed_hours': row.get('Completed Lesson Hours', 0),
                        'remaining_hours': row.get('Remaining Lesson Hours', 0),
                    }
                )

            except Exception as e:
                logging.error(f"Error creating or updating records: {e}")
                continue
            try:
                student_query = StudentQuery.objects.get(student_records=student, admin_id__isnull=True)
                student_query.delete()
                logging.info(f"Deleted Duplicate StudentQuery with no admin_id")
            except StudentQuery.DoesNotExist:
                logging.error(f"StudentQuery with no admin_id does not exist")
                logging.info(f"StudentQuery created or updated for student: {student}")

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
