import os
import django
import pandas as pd
import numpy as np
from faker import Faker
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from django.db import IntegrityError

# Import your models
from main_app.models import CustomUser, Campus, Course, ClassSchedule, LearningRecord, PaymentRecord, Student, Teacher

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
django.setup()

# Create a Faker generator
fake = Faker()

def process_data(excel_file, is_teacher, is_chinese_data=False):
    try:
        df = pd.read_excel(excel_file)
        print("Dataframe loaded successfully with {} rows.".format(len(df)))
    except Exception as e:
        print(f"Failed to read Excel file: {str(e)}")
        return None  # Return early if the file cannot be processed

    if is_chinese_data:
        df.columns = [
            'Index', 'Full Name', 'Class', 'Campus', 'Payment', 'Period', 
            'Total Periods', 'Salesperson', 'Total Lessons', 'Lessons Taken', 
            'Remaining Lessons', 'Next Payment Date', 'Teacher'
        ]

    fake_data = []

    if is_teacher:
        file = open('fake_users.txt', 'w')
        print("Opened file for writing teacher login information.")

    for index, row in df.iterrows():
        first_name = row['Full Name'].split()[0]
        last_name = row['Full Name'].split()[-1]
        email = row['Email'] if not is_chinese_data else fake.email()

        if is_teacher:
            password = get_random_string(12)
            hashed_password = make_password(password)
            file.write(f"Email: {email}, Password: {password}\n")
            print(f"Processed teacher {email} - login info written to file.")
        else:
            password = None
            hashed_password = None
            print(f"Processed student {email} - no login info required.")

        # Create or update Campus
        campus_name = row['Campus'] if not is_chinese_data else row['校区']
        campus, created = Campus.objects.get_or_create(name=campus_name)
        if created:
            print(f"Created new campus: {campus_name}")

        # Create or update Course
        course_name = row['Class'] if not is_chinese_data else row['班级']
        course, created = Course.objects.get_or_create(name=course_name)
        if created:
            print(f"Created new course: {course_name}")

        # Create or update ClassSchedule
        class_schedule, created = ClassSchedule.objects.get_or_create(course=course, campus=campus)
        if created:
            print(f"Created new class schedule for course {course_name} at campus {campus_name}")

        # Create or update PaymentRecords
        payment_amount = row['Payment'] if not is_chinese_data else row['缴费']
        next_payment_date = row['Next Payment Date'] if not is_chinese_data else row['下次缴费时间（课程结束前1月）']
        payment_record, created = PaymentRecord.objects.get_or_create(
            user_email=email,
            defaults={'amount': payment_amount, 'next_payment_date': next_payment_date}
        )
        if created:
            print(f"Created new payment record for {email}")

        # Create or update LearningRecords
        learning_record, created = LearningRecord.objects.get_or_create(
            user_email=email,
            defaults={
                'total_lessons': row['Total Lessons'] if not is_chinese_data else row['总课次'],
                'lessons_taken': row['Lessons Taken'] if not is_chinese_data else row['已上课次'],
                'remaining_lessons': row['Remaining Lessons'] if not is_chinese_data else row['剩余课次']
            }
        )
        if created:
            print(f"Created new learning record for {email}")

        # Create CustomUser
        user_data = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'password': hashed_password,
            'profile_pic': '/media/default.jpg',
            'gender': row['Gender'] if not is_chinese_data else fake.random_element(elements=('Male', 'Female')),
            'address': row['Address'] if not is_chinese_data else fake.address().replace('\n', ', '),
            'cell_number': row['Cell Number'] if not is_chinese_data else fake.phone_number(),
            'home_number': row['Home Number'] if not is_chinese_data else fake.phone_number(),
            'is_teacher': is_teacher,
            'user_type': 2 if is_teacher else 3,  # Assuming 2 is for teachers and 3 is for students
            'fcm_token': ''
        }

        try:
            user = CustomUser.objects.create_user(**user_data)
            fake_data.append(user_data)
            print(f"User {email} created and added to fake data.")
        except IntegrityError as e:
            print(f"Error: Duplicate or invalid data for email {email} - {str(e)}")
            continue

        # Create or update Student or Teacher
        if is_teacher:
            teacher, created = Teacher.objects.get_or_create(user=user)
            if created:
                print(f"Created new teacher profile for {email}")
        else:
            student, created = Student.objects.get_or_create(user=user)
            if created:
                print(f"Created new student profile for {email}")

    if is_teacher:
        file.close()
        print("Teacher login file closed.")

    print("Data processing complete for", "teachers" if is_teacher else "students")
    return fake_data  # Returning fake_data could be more useful than just the file path

# Example usage
# process_data('path_to_excel_file.xlsx', is_teacher=True, is_chinese_data=True)
