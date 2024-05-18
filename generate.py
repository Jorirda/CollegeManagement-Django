import os
import django
import pandas as pd
from faker import Faker
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from django.db import IntegrityError
import logging

# Import your models
from main_app.models import CustomUser, Campus, Course, LearningRecord, PaymentRecord, Student, Teacher

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
django.setup()

# Create a Faker generator
fake = Faker()

# Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        logging.info("Dataframe loaded successfully with %d rows.", len(df))
    except Exception as e:
        logging.error("Failed to read Excel file: %s", str(e))
        return None

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
        
        logging.debug("Original columns: %s", df.columns)
        
        try:
            df.rename(columns=column_mapping, inplace=True)
            logging.debug("Columns after renaming: %s", df.columns)
        except KeyError as e:
            logging.error("Column not found during renaming: %s", str(e))
            return None

    required_columns = ['Full Name', 'Class', 'Campus', 'Payment', 'Next Payment Date', 'Total Lessons', 'Lessons Taken', 'Remaining Lessons']
    for column in required_columns:
        if column not in df.columns:
            logging.error("Missing expected column after renaming: %s", column)
            return None

    fake_data = []

    if is_teacher:
        with open('fake_users.txt', 'w') as file:
            logging.info("Opened file for writing teacher login information.")
            for index, row in df.iterrows():
                try:
                    full_name = row['Full Name']
                    email = row.get('Email', fake.email())

                    password = get_random_string(12)
                    hashed_password = make_password(password)
                    file.write(f"Email: {email}, Password: {password}\n")
                    logging.info("Processed teacher %s - login info written to file.", email)

                    campus_name = row['Campus']
                    campus, created = Campus.objects.get_or_create(name=campus_name)
                    if created:
                        logging.info("Created new campus: %s", campus_name)

                    class_full_name = row['Class']
                    course_name, grade_level = None, None
                    for chinese_grade, grade in grade_mapping.items():
                        if chinese_grade in class_full_name:
                            course_name = class_full_name.replace(chinese_grade, '').strip()
                            grade_level = grade
                            break

                    if course_name:
                        course, created = Course.objects.get_or_create(name=course_name)
                        if created:
                            course.level_end = grade_level
                            course.save()
                            logging.info("Created new course: %s with grade %d", course_name, grade_level)
                        else:
                            if course.level_end < grade_level:
                                course.level_end = grade_level
                                course.save()
                                logging.info("Updated existing course: %s to grade %d", course_name, grade_level)
                            else:
                                logging.info("Existing course: %s already has grade %d", course_name, course.level_end)
                    else:
                        logging.warning("Failed to parse course name and grade from: %s", class_full_name)

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
                        'remark': f"Salesperson: {row['Salesperson']}",
                        'fcm_token': ''  # default
                    }

                    try:
                        user = CustomUser.objects.create_user(**user_data)
                        fake_data.append(user_data)
                        logging.info("User %s created and added to fake data.", email)
                    except IntegrityError as e:
                        logging.error("Error: Duplicate or invalid data for email %s - %s", email, str(e))
                        continue

                    teacher, created = Teacher.objects.update_or_create(user=user)
                    if created:
                        logging.info("Created new teacher profile for %s", email)

                except KeyError as e:
                    logging.error("Missing expected column: %s", str(e))
                    continue
                except Exception as e:
                    logging.error("Unexpected error: %s", str(e))
                    continue

    else:
        for index, row in df.iterrows():
            try:
                full_name = row['Full Name']
                email = row.get('Email', fake.email())

                campus_name = row['Campus']
                campus, created = Campus.objects.get_or_create(name=campus_name)
                if created:
                    logging.info("Created new campus: %s", campus_name)

                class_full_name = row['Class']
                course_name, grade_level = None, None
                for chinese_grade, grade in grade_mapping.items():
                    if chinese_grade in class_full_name:
                        course_name = class_full_name.replace(chinese_grade, '').strip()
                        grade_level = grade
                        break

                if course_name:
                    course, created = Course.objects.get_or_create(name=course_name)
                    if created:
                        course.level_end = grade_level
                        course.save()
                        logging.info("Created new course: %s with grade %d", course_name, grade_level)
                    else:
                        if course.level_end < grade_level:
                            course.level_end = grade_level
                            course.save()
                            logging.info("Updated existing course: %s to grade %d", course_name, grade_level)
                        else:
                            logging.info("Existing course: %s already has grade %d", course_name, course.level_end)
                else:
                    logging.warning("Failed to parse course name and grade from: %s", class_full_name)

                user_data = {
                    'full_name': full_name,
                    'email': email,
                    'password': None,
                    'profile_pic': '/media/default.jpg',
                    'gender': row.get('Gender', fake.random_element(elements=('男', '女'))),
                    'address': row.get('Address', fake.address().replace('\n', ', ')),
                    'phone_number': row.get('Phone Number', fake.phone_number()),
                    'is_teacher': is_teacher,
                    'user_type': 2 if is_teacher else 3,
                    'remark': f"Salesperson: {row['Salesperson']}",
                    'fcm_token': ''  # default
                }

                try:
                    user = CustomUser.objects.create_user(**user_data)
                    fake_data.append(user_data)
                    logging.info("User %s created and added to fake data.", email)
                except IntegrityError as e:
                    logging.error("Error: Duplicate or invalid data for email %s - %s", email, str(e))
                    continue

            except KeyError as e:
                logging.error("Missing expected column: %s", str(e))
                continue
            except Exception as e:
                logging.error("Unexpected error: %s", str(e))
                continue

    logging.info("First pass data processing complete for %s", "teachers" if is_teacher else "students")
    return df

def update_student_records(df, is_chinese_data=False):
    for index, row in df.iterrows():
        try:
            full_name = row['Full Name']
            email = row.get('Email', fake.email())
            campus_name = row['Campus']
            campus = Campus.objects.get(name=campus_name)

            class_full_name = row['Class']
            course_name, grade_level = None, None
            for chinese_grade, grade in grade_mapping.items():
                if chinese_grade in class_full_name:
                    course_name = class_full_name.replace(chinese_grade, '').strip()
                    grade_level = grade
                    break

            if course_name:
                course = Course.objects.get(name=course_name)

                user = CustomUser.objects.get(email=email)
                student, created = Student.objects.update_or_create(
                    user=user,
                    campus=campus,
                    admin=user.admin,
                    course=course
                )
                if created:
                    logging.info("Created new student profile for %s", email)
                else:
                    logging.info("Updated existing student profile for %s", email)

                try:
                    learning_record, created = LearningRecord.objects.get_or_create(
                        student=student,
                        course=course,
                        defaults={
                            'total_lessons': row['Total Lessons'],
                            'lessons_taken': row['Lessons Taken'],
                            'remaining_lessons': row['Remaining Lessons']
                        }
                    )
                    if created:
                        logging.info("Created new learning record for %s and course %s", email, course.name)
                    else:
                        logging.info("Updated existing learning record for %s and course %s", email, course.name)

                    payment_record, created = PaymentRecord.objects.get_or_create(
                        student=student,
                        learning_record=learning_record,
                        defaults={
                            'amount_due': row['Payment'], 
                            'next_payment_date': row['Next Payment Date'], 
                            'remark': row['Salesperson']
                        }
                    )
                    if created:
                        logging.info("Created new payment record for %s and learning record %d", email, learning_record.id)
                    else:
                        logging.info("Updated existing payment record for %s and learning record %d", email, learning_record.id)

                except Exception as e:
                    logging.error("Error creating learning or payment record for %s: %s", email, str(e))

        except KeyError as e:
            logging.error("Missing expected column: %s", str(e))
            continue
        except Exception as e:
            logging.error("Unexpected error: %s", str(e))
            continue

    logging.info("Second pass data processing complete for students")

# Example usage
# First pass: process data and create users, courses, and campuses
df = process_data('path_to_excel_file.xlsx', is_teacher=True, is_chinese_data=True)

# Second pass: update student records with learning and payment records
if df is not None:
    update_student_records(df, is_chinese_data=True)
