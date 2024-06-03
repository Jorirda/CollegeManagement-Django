# generate.py

import os
import json
import django
import pandas as pd
import logging
from faker import Faker
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
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
        logging.FileHandler("data_processing.log", encoding='utf-8'),  # Set encoding to 'utf-8'
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

# Define required fields for each model
REQUIRED_FIELDS = {
    'CustomUser': ['姓名', '邮箱', '性别', '地址', '电话号码', '用户类型'],
    'Student': ['学生姓名', '校区', '班级', '出生日期', '注册日期', '状态'],
    'Teacher': ['授课老师', '班级', '校区', '工作类型'],
    'Session': ['开始年份', '结束年份'],
    'Campus': ['校区', '校长', '校长联系电话'],
    'Course': ['班级', '班级概述', '开始级别', '结束级别', '图片'],
    'ClassSchedule': ['班级', '课时单价', '教师', '年级', '开始时间', '结束时间', '课时', '备注'],
    'LearningRecord': ['日期', '学生', '班级', '教师', '班级安排', '学期', '开始时间', '结束时间', '课时', '星期'],
    'PaymentRecord': ['日期', '下次缴费时间\n（班级结束前1月）', '学生', '班级', '课时单价', '折后价格', '书本费', '其他费用', '应付金额', '缴费', '支付方式', '状态', '缴费人', '备注', '课时', '学习记录'],
    'RefundRecord': ['学生', '学习记录', '付款记录', '退款金额', '已退款金额', '退款原因']
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

def process_data(df, model_name, user_type):
    try:
        model_info = MODEL_COLUMN_MAPPING.get(model_name)
        if not model_info:
            raise ValueError(f"No model found for the selected type: {model_name}")

        required_columns = REQUIRED_FIELDS.get(model_name, [])
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        processed_data = []

        for index, row in df.iterrows():
            record_data = {}
            for col_name in model_info['fields'].keys():
                if col_name in df.columns:
                    record_data[model_info['fields'][col_name]] = row[col_name]
                else:
                    specific_mapping = SPECIFIC_COLUMN_MAPPING.get(model_name, {}).get(user_type, {})
                    if col_name in specific_mapping and specific_mapping[col_name] in df.columns:
                        record_data[model_info['fields'][col_name]] = row[specific_mapping[col_name]]
                    else:
                        record_data[model_info['fields'][col_name]] = fake_data(model_info['fields'][col_name], row, user_type)

            # Process Campus and Course
            if model_name == 'Student' or model_name == 'Teacher':
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

            # Handle user creation
            full_name = record_data.get('full_name', fake.name())
            email = record_data.get('email', fake.email())
            password = record_data.get('password', make_password(get_random_string(12)))

            user_data = {
                'full_name': full_name,
                'email': email,
                'password': password,
                'profile_pic': record_data.get('profile_pic', '/media/default.jpg'),
                'gender': record_data.get('gender', fake.random_element(elements=('男', '女'))),
                'address': record_data.get('address', fake.address().replace('\n', ', ')),
                'phone_number': record_data.get('phone_number', fake.phone_number()),
                'is_teacher': user_type == 'Teacher',
                'user_type': 2 if user_type == 'Teacher' else 3,
                'remark': record_data.get('remark', "销售人员: " + fake.name()),
                'fcm_token': record_data.get('fcm_token', '')
            }

            try:
                user = CustomUser.objects.create_user(**user_data)
                if model_name == 'Student':
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

                    # Handle LearningRecord and PaymentRecord
                    remark = user_data['remark'] if student and student.admin else None
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

                    try:
                        student_query = StudentQuery.objects.get(student_records=student, admin_id__isnull=True)
                        student_query.delete()
                        logging.info(f"Deleted Duplicate StudentQuery with no admin_id")
                    except StudentQuery.DoesNotExist:
                        logging.info(f"No duplicate StudentQuery found for student: {student}")

            except IntegrityError as e:
                logging.error(f"IntegrityError for user: {email}")
                continue

            processed_data.append(record_data)

        return True
    except Exception as e:
        logging.error(f"Error processing data: {e}")
        return False


def fake_data(field, row, user_type):
    if field == 'full_name':
        return fake.name()
    elif field == 'email':
        return fake.email()
    elif field == 'gender':
        return get_value_from_row(row, '性别', None, fake.random_element(elements=('男', '女')))
    elif field == 'address':
        return get_value_from_row(row, '地址', None, fake.address().replace('\n', ', '))
    elif field == 'phone_number':
        return get_value_from_row(row, '电话号码', None, fake.phone_number())
    elif field == 'password':
        return make_password(get_random_string(12))
    elif field == 'profile_pic':
        return '/media/default.jpg'
    elif field == 'user_type':
        return 2 if user_type == 'Teacher' else 3
    elif field == 'remark':
        return "销售人员: " + get_value_from_row(row, '销售人员', 'Unknown', fake.name())
    elif field == 'fcm_token':
        return ''
    else:
        return fake.word()

def get_value_from_row(row, column_name, default_value, fake_value):
    value = row.get(column_name)
    if pd.isna(value) or value == "":
        value = default_value if default_value is not None else fake_value
    return value

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

def main(excel_file, selected_model, user_type):
    sheets = read_excel_file(excel_file)
    if selected_model not in MODEL_COLUMN_MAPPING:
        print(f"No model mapping found for selected model: {selected_model}")
        return False

    for sheet_name, sheet_data in sheets.items():
        if sheet_name in MODEL_COLUMN_MAPPING:
            result = process_data(sheet_data, selected_model, user_type)
            if result:
                print(f"Processed data for sheet: {sheet_name}")
            else:
                print(f"Failed to process data for sheet: {sheet_name}")
                return False
        else:
            print(f"No model mapping found for sheet: {sheet_name}")
    return True

# Example usage
# main('path_to_excel_file.xlsx', 'CustomUser', 'Student')


