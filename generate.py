import os
import random
import django
import pandas as pd
import logging
from faker import Faker
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from django.db import IntegrityError
from main_app.models import CustomUser, Campus, Course, LearningRecord, Student, Teacher, PaymentRecord, StudentQuery, Session, ClassSchedule, RefundRecord
from main_app.model_column_mapping import MODEL_COLUMN_MAPPING

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
django.setup()

# Create a Faker generator
fake = Faker()
random_number = random.randint(1, 7)

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

def process_data(excel_file, auto_create_learning_record=False, auto_create_payment_record=False):
    try:
        df = pd.read_excel(excel_file)
        logging.info(f"Dataframe loaded successfully with {len(df)} rows.")
        logging.info(f"Columns in dataframe: {df.columns.tolist()}")
    except Exception as e:
        logging.error(f"Error reading Excel file: {e}")
        return None  # Return early if the file cannot be processed

    fake_data = []
    user_student_pairs = []

    for index, row in df.iterrows():
        try:
            if '出生日期' not in row:
                logging.warning(f"Missing '出生日期' column in row {index}. Using fake data.")
                date_of_birth = fake.date_of_birth(minimum_age=10, maximum_age=18)
            else:
                date_of_birth = row.get('出生日期')

            full_name = row.get('学生姓名', fake.name())
            email = row.get('邮箱', fake.email())
            gender = row.get('性别', fake.random_element(elements=('男', '女')))
            address = row.get('地址', fake.address().replace('\n', ', '))
            phone_number = row.get('电话号码', fake.phone_number())
            reg_date = row.get('注册日期', fake.date_this_year())
            status = row.get('状态', 'active')

            campus_name = row.get('校区', 'Unknown Campus')
            campus, _ = Campus.objects.get_or_create(name=campus_name)

            class_name = row.get('班级', 'Unknown Class')
            course_name, grade_level = None, None
            for chinese_grade, grade in grade_mapping.items():
                if chinese_grade in class_name:
                    course_name = class_name.replace(chinese_grade, '').strip()
                    grade_level = grade
                    break

            if course_name:
                course, created = Course.objects.get_or_create(name=course_name)
                if created or course.level_end < grade_level:
                    course.level_end = grade_level
                    course.save()
                logging.info(f"Course retrieved or created: {course_name}")

            remark = "销售人员: " + row.get('销售人员', 'Unknown')

            # Create or update CustomUser
            user, created = CustomUser.objects.update_or_create(
                email=email,
                defaults={
                    'full_name': full_name,
                    'password': make_password('password123'),
                    'gender': gender,
                    'address': address,
                    'phone_number': phone_number,
                    'user_type': 3,  # Assuming 3 is for students
                    'remark': remark
                }
            )

            # Create or update Student
            student, created = Student.objects.update_or_create(
                admin=user,
                defaults={
                    'campus': campus,
                    'date_of_birth': date_of_birth,
                    'reg_date': reg_date,
                    'status': status
                }
            )
            # Add course to student_courses relationship
            student.courses.add(course)
            
            if auto_create_learning_record:
                LearningRecord.objects.get_or_create(
                    student=student,
                    course=course,
                    defaults={
                        'date': reg_date,
                        'semester_id': 1,  # Example value
                        'start_time': '08:00',
                        'end_time': '10:00',
                        'lesson_hours': 2,
                        'day': 'Monday'
                    }
                )

            if auto_create_payment_record:
                PaymentRecord.objects.get_or_create(
                    student=student,
                    course=course,
                    defaults={
                        'date': reg_date,
                        'amount_paid': 1000,  # Example value
                        'payment_method': 'Cash',
                        'status': 'Pending',
                        'remark': remark
                    }
                )

            user_student_pairs.append((user, student, course, row))

            # Logging
            logging.info(f"Student instance saved or updated for: {full_name}")
            logging.info(f"StudentQuery for {full_name} updated successfully.")

        except KeyError as e:
            logging.error(f"KeyError: {e}")
            continue
        except Exception as e:
            logging.error(f"Exception: {e}")
            continue

    return fake_data

def process_course(excel_file):
    try:
        df = pd.read_excel(excel_file)
        logging.info(f"Dataframe loaded successfully with {len(df)} rows.")
    except Exception as e:
        logging.error(f"Error reading Excel file: {e}")
        return None

    for index, row in df.iterrows():
        try:
            class_name = row.get('班级', 'Unknown Class')
            course_name, grade_level = None, None
            for chinese_grade, grade in grade_mapping.items():
                if chinese_grade in class_name:
                    course_name = class_name.replace(chinese_grade, '').strip()
                    grade_level = grade
                    break

            if course_name:
                course, created = Course.objects.get_or_create(name=course_name)
                if created or course.level_end < grade_level:
                    course.level_end = grade_level
                    course.save()
                logging.info(f"Course retrieved or created: {course_name}")

        except Exception as e:
            logging.error(f"Exception: {e}")
            continue

def process_learning_record(excel_file):
    try:
        df = pd.read_excel(excel_file)
        logging.info(f"Dataframe loaded successfully with {len(df)} rows.")
    except Exception as e:
        logging.error(f"Error reading Excel file: {e}")
        return None

    for index, row in df.iterrows():
        try:
            student_name = row.get('学生姓名')
            student_salesperson = row.get('销售人员')
            course_name = row.get('班级')
            teacher_name = row.get('教师')

            student = Student.objects.get(admin__full_name=student_name, admin__remark__icontains=student_salesperson)
            course = Course.objects.get(name=course_name)
            teacher = Teacher.objects.get(admin__full_name=teacher_name)

            LearningRecord.objects.update_or_create(
                student=student,
                course=course,
                defaults={
                    'date': row.get('日期'),
                    'teacher': teacher,
                    'schedule_record': row.get('班级安排'),
                    'semester': row.get('学期'),
                    'start_time': row.get('开始时间'),
                    'end_time': row.get('结束时间'),
                    'lesson_hours': row.get('课时'),
                    'day': row.get('星期')
                }
            )

            logging.info(f"LearningRecord instance saved or updated for student: {student_name}")

        except Student.DoesNotExist:
            logging.error(f"Student {student_name} with salesperson {student_salesperson} does not exist.")
        except Course.DoesNotExist:
            logging.error(f"Course {course_name} does not exist.")
        except Teacher.DoesNotExist:
            logging.error(f"Teacher {teacher_name} does not exist.")
        except Exception as e:
            logging.error(f"Exception: {e}")
            continue

def process_payment_record(excel_file):
    try:
        df = pd.read_excel(excel_file)
        logging.info(f"Dataframe loaded successfully with {len(df)} rows.")
    except Exception as e:
        logging.error(f"Error reading Excel file: {e}")
        return None

    for index, row in df.iterrows():
        try:
            student_name = row.get('学生姓名')
            student_salesperson = row.get('销售人员')
            course_name = row.get('班级')
            teacher_name = row.get('教师')

            student = Student.objects.get(admin__full_name=student_name, admin__remark__icontains=student_salesperson)
            course = Course.objects.get(name=course_name)
            teacher = Teacher.objects.get(admin__full_name=teacher_name)

            PaymentRecord.objects.update_or_create(
                student=student,
                course=course,
                defaults={
                    'date': row.get('日期'),
                    'next_payment_date': row.get('下次缴费时间\n（课程结束前1月）'),
                    'amount_paid': row.get('缴费'),
                    'payment_method': row.get('支付方式'),
                    'status': row.get('状态'),
                    'payee': row.get('缴费人'),
                    'remark': row.get('备注'),
                    'lesson_hours': row.get('课时'),
                    'lesson_unit_price': row.get('课时单价'),
                    'discounted_price': row.get('折后价格'),
                    'book_costs': row.get('书本费'),
                    'other_fee': row.get('其他费用'),
                    'amount_due': row.get('应付金额')
                }
            )

            logging.info(f"PaymentRecord instance saved or updated for student: {student_name}")

        except Student.DoesNotExist:
            logging.error(f"Student {student_name} with salesperson {student_salesperson} does not exist.")
        except Course.DoesNotExist:
            logging.error(f"Course {course_name} does not exist.")
        except Teacher.DoesNotExist:
            logging.error(f"Teacher {teacher_name} does not exist.")
        except Exception as e:
            logging.error(f"Exception: {e}")
            continue

def main(excel_file, selected_model, user_type=None, auto_create_learning_record=False, auto_create_payment_record=False):
    if selected_model == 'Student':
        process_data(excel_file, auto_create_learning_record, auto_create_payment_record)
    elif selected_model == 'Teacher':
        process_data(excel_file, auto_create_learning_record, auto_create_payment_record)
    elif selected_model == 'CustomUser' and user_type in ['Student', 'Teacher']:
        process_data(excel_file, auto_create_learning_record, auto_create_payment_record)
    elif selected_model == 'Course':
        process_course(excel_file)
    elif selected_model == 'LearningRecord':
        process_learning_record(excel_file)
    elif selected_model == 'PaymentRecord':
        process_payment_record(excel_file)
    else:
        sheets = read_excel_file(excel_file)
        process_all_sheets(sheets, MODEL_COLUMN_MAPPING)

def read_excel_file(excel_file):
    sheets = pd.read_excel(excel_file, sheet_name=None)
    return sheets

def process_all_sheets(sheets, model_column_mapping):
    for sheet_name, sheet_data in sheets.items():
        if sheet_name in model_column_mapping:
            process_sheet(sheet_name, sheet_data, model_column_mapping[sheet_name])
        else:
            logging.warning(f"No model mapping found for sheet: {sheet_name}")

def process_sheet(sheet_name, sheet_data, model_info):
    model = model_info['model']
    field_mapping = model_info['fields']

    for index, row in sheet_data.iterrows():
        data = {}
        for col, field in field_mapping.items():
            data[field] = row[col]
        
        try:
            model.objects.update_or_create(**data)
            logging.info(f"{model.__name__} record processed: {data}")
        except IntegrityError as e:
            logging.error(f"IntegrityError for {model.__name__}: {e}")
        except Exception as e:
            logging.error(f"Error for {model.__name__}: {e}")

def fake_value(column_name):
    fake = Faker()
    if column_name == '出生日期':
        return fake.date_of_birth(minimum_age=10, maximum_age=18).isoformat()
    elif column_name == '注册日期':
        return fake.date_this_year().isoformat()
    elif column_name == '状态':
        return 'Active'
    # Add more cases for other columns as needed
    return fake.word()
