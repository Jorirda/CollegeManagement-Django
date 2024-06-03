import os
import django
import pandas as pd
import logging
from faker import Faker
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from django.db import IntegrityError
from main_app.models import CustomUser, Campus, Course, LearningRecord, Student, Teacher, PaymentRecord, StudentQuery
from main_app.model_column_mapping import MODEL_COLUMN_MAPPING

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

def get_value_from_row(row, column_name, default_value=None, fake_value=None):
    value = row.get(column_name)
    if pd.isna(value) or value == "":
        value = default_value if default_value is not None else fake_value
    return value

def process_data(excel_file, selected_model):
    try:
        df = pd.read_excel(excel_file)
        logging.info(f"Dataframe loaded successfully with {len(df)} rows.")
    except Exception as e:
        logging.error(f"Error reading Excel file: {e}")
        return None  # Return early if the file cannot be processed

    required_columns = MODEL_COLUMN_MAPPING[selected_model]['fields'].keys()
    for column in required_columns:
        if column not in df.columns:
            logging.warning(f"Missing required column: {column}. Using fake data.")
            fake_value = fake.date_of_birth(minimum_age=10, maximum_age=18).isoformat() if column == '出生日期' else ''
            df[column] = df.apply(lambda x: fake_value, axis=1)

    fake_data = []
    user_student_pairs = []

    for index, row in df.iterrows():
        try:
            full_name = get_value_from_row(row, '学生姓名', fake.name())
            email = get_value_from_row(row, '邮箱', fake.email())

            password = get_random_string(12)
            hashed_password = make_password(password)

            campus_name = get_value_from_row(row, '校区', fake.company())
            campus, _ = Campus.objects.get_or_create(name=campus_name)
            logging.info(f"Campus retrieved or created: {campus_name}")

            class_full_name = get_value_from_row(row, '班级', fake.job())
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
                'gender': get_value_from_row(row, '性别', fake.random_element(elements=('男', '女'))),
                'address': get_value_from_row(row, '地址', fake.address().replace('\n', ', ')),
                'phone_number': get_value_from_row(row, '电话号码', fake.phone_number()),
                'is_teacher': selected_model == 'Teacher',
                'user_type': 2 if selected_model == 'Teacher' else 3,  
                'remark': "Salesperson: " + get_value_from_row(row, '销售人员', fake.name()),
                'fcm_token': ''  
            }

            try:
                user, user_created = CustomUser.objects.get_or_create(
                    email=email,
                    defaults=user_data
                )
                if not user_created:
                    for key, value in user_data.items():
                        setattr(user, key, value)
                    user.save()
                fake_data.append(user_data)
                logging.info(f"User {'created' if user_created else 'updated'}: {email}")
            except IntegrityError:
                logging.error(f"IntegrityError for user: {email}")
                continue

            if selected_model == 'Teacher':
                Teacher.objects.get_or_create(admin=user)
                logging.info(f"Teacher profile created for: {email}")
            else:
                student, student_created = Student.objects.get_or_create(
                    admin=user,
                    defaults={
                        'campus': campus,
                        'course': course,
                        'date_of_birth': get_value_from_row(row, '出生日期', fake_value=fake.date_of_birth(minimum_age=10, maximum_age=18).isoformat()),
                        'reg_date': get_value_from_row(row, '注册日期', fake_value=fake.date_this_year().isoformat()),
                        'status': get_value_from_row(row, '状态', fake_value='active')
                    }
                )
                if not student_created:
                    student.campus = campus
                    student.course = course
                    student.date_of_birth = get_value_from_row(row, '出生日期', fake_value=fake.date_of_birth(minimum_age=10, maximum_age=18).isoformat())
                    student.reg_date = get_value_from_row(row, '注册日期', fake_value=fake.date_this_year().isoformat())
                    student.status = get_value_from_row(row, '状态', fake_value='active')
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

    logging.info("User-student pairs processed: %s", user_student_pairs)

    for user, student, course, row in user_student_pairs:
        try:
            remark = user.remark if student and student.admin else None
            lesson_unit_price = row.get('课时单价', 0)
            ls, created = LearningRecord.objects.get_or_create(
                student=student,
                course=course,
                defaults={
                    'date': user.date_joined,
                }
            )
            PaymentRecord.objects.get_or_create(
                student=student,
                course=course,
                defaults={
                    'date': user.date_joined,
                    'next_payment_date': get_value_from_row(row, '下次缴费时间\n（班级结束前1月）', fake_value=fake.date_this_year().isoformat()),
                    'amount_paid': get_value_from_row(row, '缴费', fake_value=0),
                    'payee': full_name,
                    'status': 'Currently Learning',
                    'lesson_hours': get_value_from_row(row, '总课次', fake_value=0),
                    'lesson_unit_price': lesson_unit_price,
                    'discounted_price': lesson_unit_price,
                    'book_costs': 0,
                    'other_fee': 0,
                    'amount_due': 0,
                    'remark': remark,
                }
            )
            
            StudentQuery.objects.get_or_create(
                student_records=student,
                registered_courses=course,
                admin=user,
                defaults={
                    'paid_class_hours': get_value_from_row(row, '总课次', fake_value=0),
                    'completed_hours': get_value_from_row(row, '已上课次', fake_value=0),
                    'remaining_hours': get_value_from_row(row, '剩余课次', fake_value=0),
                }
            )
            logging.info(f"StudentQuery created for student: {student}")
        except Exception as e:
            logging.error(f"Error creating LearningRecord: {e}")
            continue

    return fake_data

# Example usage
# process_data('path_to_excel_file.xlsx', selected_model='Student')
