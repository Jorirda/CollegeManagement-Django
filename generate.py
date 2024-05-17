import os
import django
import pandas as pd
from faker import Faker
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from django.db import IntegrityError
from django.utils.translation import gettext as _
# Import your models
from main_app.models import CustomUser, Campus, Course, LearningRecord, PaymentRecord, Student, Teacher

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
        print("Dataframe loaded successfully with {} rows.".format(len(df)))
    except Exception as e:
        print(f"Failed to read Excel file: {str(e)}")
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
        
        # Debug: Print original column names
        print("Original columns:", df.columns)
        
        try:
            df.rename(columns=column_mapping, inplace=True)
            # Debug: Print columns after renaming
            print("Columns after renaming:", df.columns)
        except KeyError as e:
            print(f"Column not found during renaming: {str(e)}")
            return None

    # Check if required columns are present after renaming
    required_columns = ['Full Name', 'Class', 'Campus', 'Payment', 'Next Payment Date', 'Total Lessons', 'Lessons Taken', 'Remaining Lessons']
    for column in required_columns:
        if column not in df.columns:
            print(f"Missing expected column after renaming: {column}")
            return None

    fake_data = []

    if is_teacher:
        file = open('fake_users.txt', 'w')
        print("Opened file for writing teacher login information.")

    for index, row in df.iterrows():
        try:
            full_name = row['Full Name']
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
            campus_name = row['Campus']
            campus, created = Campus.objects.get_or_create(name=campus_name)
            if created:
                print(f"Created new campus: {campus_name}")

            # Create or update Course
            class_full_name = row['Class']
            course_name, grade_level = None, None
            
            # Extract course name and grade level
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
                    print(f"Created new course: {course_name} with grade {grade_level}")
                else:
                    # Only update the course if the new grade level is higher
                    if course.level_end < grade_level:
                        course.level_end = grade_level
                        course.save()
                        print(f"Updated existing course: {course_name} to grade {grade_level}")
                    else:
                        print(f"Existing course: {course_name} already has grade {course.level_end}")
            else:
                print(f"Failed to parse course name and grade from: {class_full_name}")

            # Create CustomUser
            user_data = {
                'full_name': full_name,
                'email': email,
                'password': hashed_password,
                'profile_pic': '/media/default.jpg',
                'gender': row['Gender'] if not is_chinese_data else fake.random_element(elements=('男', '女')),
                'address': row['Address'] if not is_chinese_data else fake.address().replace('\n', ', '),
                'phone_number': row['Phone Number'] if not is_chinese_data else fake.phone_number(),
                'is_teacher': is_teacher,
                # 'status' :  _('Currently Learning'),
                'user_type': 2 if is_teacher else 3,  # Assuming 2 is for teachers and 3 is for students
                'remark': _('Salesperson:') + row['Salesperson'],
                'fcm_token': '' #default
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
                teacher, created = Teacher.objects.update_or_create(user=user)
                if created:
                    print(f"Created new teacher profile for {email}")
            else:
                student, created = Student.objects.update_or_create(user=user, campus_id=campus, admin=user.admin, course_id=course)
                if created:
                    print(f"Created new student profile for {email}")
                else:
                    print(f"Updated existing student profile for {email}")

                # Create LearningRecords and PaymentRecords for each course
                try:
                    learning_record, created = LearningRecord.objects.get_or_create(
                        student_id=student,
                        course_id=course,
                        defaults={
                            'total_lessons': row['Total Lessons'],
                            'lessons_taken': row['Lessons Taken'],
                            'remaining_lessons': row['Remaining Lessons']
                        }
                    )
                    if created:
                        print(f"Created new learning record for {email} and course {course.name}")
                    else:
                        print(f"Updated existing learning record for {email} and course {course.name}")

                    payment_record, created = PaymentRecord.objects.get_or_create(
                        student_id=student,
                        learning_record_id=learning_record,
                        defaults={'amount_due': row['Payment'], 'next_payment_date': row['Next Payment Date'], 'remark': row['Salesperson']}
                    )
                    if created:
                        print(f"Created new payment record for {email} and learning record {learning_record.id}")
                    else:
                        print(f"Updated existing payment record for {email} and learning record {learning_record.id}")

                except Exception as e:
                    print(f"Error creating learning or payment record for {email}: {str(e)}")

        except KeyError as e:
            print(f"Missing expected column: {str(e)}")
            continue
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            continue

    if is_teacher:
        file.close()
        print("Teacher login file closed.")

    print("Data processing complete for", "teachers" if is_teacher else "students")
    return fake_data  # Returning fake_data could be more useful than just the file path

# Example usage
# process_data('path_to_excel_file.xlsx', is_teacher=True, is_chinese_data=True)
