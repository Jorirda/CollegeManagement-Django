import os
import django
import pandas as pd
import logging
from faker import Faker
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from django.db import IntegrityError
from main_app.models import *
from main_app.model_column_mapping import MODEL_COLUMN_MAPPING  # Ensure correct import

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

def read_excel_file(excel_file):
    sheets = pd.read_excel(excel_file, sheet_name=None)
    return sheets

def process_sheet(sheet_name, sheet_data, model_info):
    model = model_info['model']
    field_mapping = model_info['fields']
    
    for index, row in sheet_data.iterrows():
        data = {}
        for col, field in field_mapping.items():
            if '__' in field:
                related_model_field, related_field = field.split('__')
                related_model = model._meta.get_field(related_model_field).related_model
                related_obj = related_model.objects.get(**{related_field: row[col]})
                data[related_model_field] = related_obj
            else:
                data[field] = row[col]
        
        try:
            obj, created = model.objects.update_or_create(**data)
            logging.info(f"{'Created' if created else 'Updated'} {model.__name__}: {obj}")
        except IntegrityError as e:
            logging.error(f"IntegrityError for {model.__name__}: {e}")
        except Exception as e:
            logging.error(f"Error for {model.__name__}: {e}")

def process_all_sheets(sheets, model_column_mapping):
    for sheet_name, sheet_data in sheets.items():
        if sheet_name in model_column_mapping:
            process_sheet(sheet_name, sheet_data, model_column_mapping[sheet_name])
        else:
            logging.warning(f"No model mapping found for sheet: {sheet_name}")

def get_value_from_row(row, column_name, default_value, fake_value):
    value = row.get(column_name)
    if pd.isna(value) or value == "":
        value = default_value if default_value is not None else fake_value
    return value

def process_data(excel_file, is_teacher, is_chinese_data=False):
    try:
        df = pd.read_excel(excel_file)
        logging.info(f"Dataframe loaded successfully with {len(df)} rows.")
    except Exception as e:
        logging.error(f"Error reading Excel file: {e}")
        return None  # Return early if the file cannot be processed

    if is_chinese_data:
        # Mapping Chinese columns is handled by MODEL_COLUMN_MAPPING
        column_mapping = {v: k for k, v in MODEL_COLUMN_MAPPING.items()}
        df.rename(columns=column_mapping, inplace=True)
        logging.info("Columns renamed for Chinese data.")

    required_columns = ['学生姓名', '班级', '校区', '缴费', '下次缴费时间\n（课程结束前1月）', '总课次', '已上课次', '剩余课次']
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
            full_name = get_value_from_row(row, '学生姓名', None, fake.name())
            email = get_value_from_row(row, '邮箱', None, fake.email())

            if is_teacher:
                password = get_random_string(12)
                hashed_password = make_password(password)
                file.write(f"Email: {email}, Password: {password}\n")
                logging.info(f"Processed teacher {email} - login info written to file.")
            else:
                password = None
                hashed_password = None
                logging.info(f"Processed student {email} - no login info required.")

            campus_name = get_value_from_row(row, '校区', 'Unknown Campus', fake.company())
            campus, _ = Campus.objects.get_or_create(name=campus_name)
            logging.info(f"Campus retrieved or created: {campus_name}")

            class_full_name = get_value_from_row(row, '班级', 'Unknown Class', fake.job())
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
                'gender': get_value_from_row(row, '性别', None, fake.random_element(elements=('男', '女'))),
                'address': get_value_from_row(row, '地址', None, fake.address().replace('\n', ', ')),
                'phone_number': get_value_from_row(row, '电话号码', None, fake.phone_number()),
                'is_teacher': is_teacher,
                'user_type': 2 if is_teacher else 3,  
                'remark': "销售人员: " + get_value_from_row(row, '销售人员', 'Unknown', fake.name()),
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
                Teacher.objects.get_or_create(admin=user)
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
                total_price = get_value_from_row(row, '应付金额', 0, 2180)
                total_lesson_hours = get_value_from_row(row, '总课次', 0, 100)
                
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
                        'next_payment_date': get_value_from_row(row, '下次缴费时间\n（课程结束前1月）', fake.date_this_year(), fake.date_this_year()),
                        'amount_paid': get_value_from_row(row, '缴费', 0, fake.random_int(min=1000, max=5000)),
                        'payee': get_value_from_row(row, '学生姓名', 'Unknown', fake.name()),
                        'status': 'Currently Learning',
                        'lesson_hours': total_lesson_hours,
                        'lesson_unit_price': lesson_unit_price,
                        'discounted_price': discounted_price,
                        'book_costs': get_value_from_row(row, '书本费', 0, fake.random_int(min=50, max=500)),
                        'other_fee': get_value_from_row(row, '其他费用', 0, fake.random_int(min=50, max=500)),
                        'amount_due': total_price,
                        'payment_method': get_value_from_row(row, '支付方式', 'Please Update', 'Cash'),
                        'remark': remark,
                        'total_semester': get_value_from_row(row, '累计报名期次', 1, fake.random_int(min=1, max=8))
                    }
                )

                sq, created = StudentQuery.objects.update_or_create(
                    student_records=student,
                    registered_courses=course,
                    admin=user,
                    learning_records=ls,
                    payment_records=ps,
                    defaults={
                        'num_of_classes': get_value_from_row(row, '课程数量', 1, fake.random_int(min=1, max=10)),
                        'paid_class_hours': total_lesson_hours,
                        'completed_hours': get_value_from_row(row, '已上课次', 0, fake.random_int(min=0, max=total_lesson_hours)),
                        'remaining_hours': get_value_from_row(row, '剩余课次', 0, total_lesson_hours - get_value_from_row(row, '已上课次', 0, 0)),
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

def main(excel_file):
    sheets = read_excel_file(excel_file)
    process_all_sheets(sheets, MODEL_COLUMN_MAPPING)
    # Example usage for current process_data function
    process_data(excel_file, is_teacher=False, is_chinese_data=True)

# Example usage
# main('path_to_excel_file.xlsx')
