from datetime import datetime, timedelta
import os
import random
import django
import pandas as pd
from faker import Faker
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from django.db import IntegrityError
from main_app.models import CustomUser, Campus, Course, LearningRecord, Student, Teacher, PaymentRecord, StudentQuery, Session, ClassSchedule, RefundRecord
from main_app.model_column_mapping import MODEL_COLUMN_MAPPING
from django.utils.translation import gettext_lazy as _

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
django.setup()

# Create a Faker generator
fake = Faker()
random_number = random.randint(1, 7)

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

def safe_get(row, key, default=None):
    """ Helper function to safely get a value from a row """
    return row.get(key) if pd.notna(row.get(key)) else default

def process_data(excel_file, auto_create_learning_record=False, auto_create_payment_record=False, user_type='Student'):
    try:
        df = pd.read_excel(excel_file)
        print(f"Dataframe loaded successfully with {len(df)} rows.")
        print(f"Columns in dataframe: {df.columns.tolist()}")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None  # Return early if the file cannot be processed

    fake_data = []
    user_student_pairs = []

    for index, row in df.iterrows():
        try:
            date_of_birth = safe_get(row, '出生日期', fake.date_of_birth(minimum_age=10, maximum_age=18))
            full_name = safe_get(row, '学生姓名', fake.name())
            email = safe_get(row, '邮箱', fake.email())
            gender = safe_get(row, '性别', fake.random_element(elements=('男', '女')))
            address = safe_get(row, '地址', fake.address().replace('\n', ', '))
            phone_number = safe_get(row, '电话号码', fake.phone_number())
            reg_date = safe_get(row, '注册日期', fake.date_this_year())
            status = safe_get(row, '状态', 'active')

            campus_name = safe_get(row, '校区', 'Unknown Campus')
            campus, _ = Campus.objects.get_or_create(name=campus_name)

            class_name = safe_get(row, '班级', 'Unknown Class')
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
                print(f"Course retrieved or created: {course_name}")

            remark = "销售人员: " + safe_get(row, '销售人员', 'Unknown')

            # Create or update CustomUser
            user, created = CustomUser.objects.update_or_create(
                email=email,
                defaults={
                    'full_name': full_name,
                    'password': make_password('password123'),
                    'gender': gender,
                    'address': address,
                    'phone_number': phone_number,
                    'user_type': 2 if user_type == 'Teacher' else 3,  # Assuming 2 is for teachers and 3 is for students
                    'remark': remark
                }
            )

            if user_type == 'Teacher':
                teacher, created = Teacher.objects.update_or_create(
                    admin=user,
                    defaults={
                        'campus': campus,
                        'work_type': safe_get(row, '工作类型', 'Full-Time')
                    }
                )
                teacher.courses.add(course)
                print(f"Teacher instance saved or updated for: {full_name}")

                # Save teacher credentials to file
                with open("teacher_credentials.txt", "a") as file:
                    file.write(f"Name: {full_name}, Email: {email}, Password: password123\n")

            elif user_type == 'Student':
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
                            'amount_paid': 2180,  # Example value
                            'payment_method': 'Alipay',
                            'status': 'Pending',
                            'remark': remark
                        }
                    )

                user_student_pairs.append((user, student, course, row))
                print(f"Student instance saved or updated for: {full_name}")
                print(f"StudentQuery for {full_name} updated successfully.")

        except KeyError as e:
            print(f"KeyError: {e}")
            continue
        except Exception as e:
            print(f"Exception: {e}")
            continue

    return fake_data

def process_course(excel_file):
    try:
        df = pd.read_excel(excel_file)
        print(f"Dataframe loaded successfully with {len(df)} rows.")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None

    for index, row in df.iterrows():
        try:
            class_name = safe_get(row, '班级', 'Unknown Class')
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
                print(f"Course retrieved or created: {course_name}")

        except Exception as e:
            print(f"Exception: {e}")
            continue

def process_learning_record(excel_file):
    try:
        df = pd.read_excel(excel_file)
        print(f"Dataframe loaded successfully with {len(df)} rows.")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None

    for index, row in df.iterrows():
        try:
            student_name = safe_get(row, '学生姓名')
            student_salesperson = safe_get(row, '销售人员')
            class_name = safe_get(row, '班级', 'Unknown Class')
            teacher_name = safe_get(row, '教师')

            course_name, _ = None, None
            for chinese_grade, grade in grade_mapping.items():
                if chinese_grade in class_name:
                    course_name = class_name.replace(chinese_grade, '').strip()
                    break

            student = Student.objects.get(admin__full_name=student_name, admin__remark__icontains=student_salesperson)
            course = Course.objects.get(name=course_name)
            teacher = Teacher.objects.filter(admin__full_name=teacher_name).first()

            LearningRecord.objects.update_or_create(
                student=student,
                course=course,
                defaults={
                    'date': safe_get(row, '日期', pd.Timestamp.now().strftime('%Y-%m-%d')),
                    'teacher': teacher,
                    'schedule_record': safe_get(row, '班级安排'),
                    'semester_id': safe_get(row, '学期', 1),
                    'start_time': safe_get(row, '开始时间', '08:00'),
                    'end_time': safe_get(row, '结束时间', '10:00'),
                    'lesson_hours': safe_get(row, '课时', 2),
                    'day': safe_get(row, '星期', 'Monday')
                }
            )

            print(f"LearningRecord instance saved or updated for student: {student_name}")

        except Student.DoesNotExist:
            print(f"Student {student_name} with salesperson {student_salesperson} does not exist.")
        except Course.DoesNotExist:
            print(f"Course {course_name} does not exist.")
        except Exception as e:
            print(f"Exception: {e}")
            continue

def process_payment_record(excel_file):
    try:
        df = pd.read_excel(excel_file)
        print(f"Dataframe loaded successfully with {len(df)} rows.")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None

    for index, row in df.iterrows():
        try:
            student_name = safe_get(row, '学生姓名')
            student_salesperson = safe_get(row, '销售人员')
            class_name = safe_get(row, '班级', 'Unknown Class')
            teacher_name = safe_get(row, '教师')

            course_name, _ = None, None
            for chinese_grade, grade in grade_mapping.items():
                if chinese_grade in class_name:
                    course_name = class_name.replace(chinese_grade, '').strip()
                    break

            student = Student.objects.get(admin__full_name=student_name, admin__remark__icontains=student_salesperson)
            course = Course.objects.get(name=course_name)
            teacher = Teacher.objects.filter(admin__full_name=teacher_name).first()

            # Calculate lesson_hours from amount_paid and lesson_unit_price if not provided
            amount_paid = safe_get(row, '缴费', 2180)
            lesson_unit_price = safe_get(row, '课时单价', 2180)
            lesson_hours = 20

            # Calculate amount_due
            discounted_price = safe_get(row, '折后价格', 2180)
            book_costs = safe_get(row, '书本费', 0)
            other_fee = safe_get(row, '其他费用', 0)
            amount_due = lesson_unit_price + book_costs + other_fee - amount_paid

            PaymentRecord.objects.update_or_create(
                student=student,
                course=course,
                defaults={
                    'date': safe_get(row, '日期', pd.Timestamp.now().strftime('%Y-%m-%d')),
                    'next_payment_date': safe_get(row, '下次缴费时间\n（课程结束前1月）', (pd.Timestamp.now() + pd.DateOffset(months=1)).strftime('%Y-%m-%d')),
                    'amount_paid': amount_paid,  # Example value
                    'payment_method': safe_get(row, '支付方式', 'Alipay'),
                    'status': safe_get(row, '状态', 'Pending'),
                    'payee': safe_get(row, '缴费人', 'Student'),
                    'remark': safe_get(row, '备注', ''),
                    'lesson_hours': safe_get(row, '课时', lesson_hours),
                    'lesson_unit_price': lesson_unit_price,
                    'discounted_price': discounted_price,
                    'book_costs': book_costs,
                    'other_fee': other_fee,
                    'amount_due': safe_get(row, '应付金额', amount_due)  # Example calculation
                }
            )

            print(f"PaymentRecord instance saved or updated for student: {student_name}")

        except Student.DoesNotExist:
            print(f"Student {student_name} with salesperson {student_salesperson} does not exist.")
        except Course.DoesNotExist:
            print(f"Course {course_name} does not exist.")
        except Exception as e:
            print(f"Exception: {e}")
            continue

def process_refund_record(excel_file):
    try:
        df = pd.read_excel(excel_file)
        print(f"Dataframe loaded successfully with {len(df)} rows.")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None

    for index, row in df.iterrows():
        try:
            student_name = safe_get(row, '学生姓名')
            student_salesperson = safe_get(row, '销售人员')
            learning_record_date = safe_get(row, '学习记录日期', datetime.now().date())
            payment_record_date = safe_get(row, '付款记录日期', datetime.now().date())

            # Match student
            student = Student.objects.get(admin__full_name=student_name, admin__remark__icontains=student_salesperson)

            # Match learning record
            learning_record = LearningRecord.objects.get(student=student, date=learning_record_date)

            # Match payment record
            payment_record = PaymentRecord.objects.get(student=student, date=payment_record_date)

            # Process refund record
            RefundRecord.objects.update_or_create(
                student=student,
                learning_records=learning_record,
                payment_records=payment_record,
                defaults={
                    'refund_amount': safe_get(row, '退款金额', 0),
                    'amount_refunded': safe_get(row, '已退款金额', 0),
                    'refund_reason': safe_get(row, '退款原因', 'N/A')
                }
            )

            print(f"RefundRecord instance saved or updated for student: {student_name}")
        
        except Student.DoesNotExist:
            print(f"Student {student_name} with salesperson {student_salesperson} does not exist.")
        except LearningRecord.DoesNotExist:
            print(f"LearningRecord with date {learning_record_date} for student {student_name} does not exist.")
        except PaymentRecord.DoesNotExist:
            print(f"PaymentRecord with date {payment_record_date} for student {student_name} does not exist.")
        except Exception as e:
            print(f"Exception: {e}")
            continue

def process_class_schedule(excel_file):
    try:
        df = pd.read_excel(excel_file)
        print(f"Dataframe loaded successfully with {len(df)} rows.")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None

    for index, row in df.iterrows():
        try:
            class_name = safe_get(row, '班级', 'Unknown Class')
            teacher_name = safe_get(row, '教师')

            # Find or create course
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
                print(f"Course retrieved or created: {course_name}")

            # Find or create teacher
            teacher = None
            if teacher_name:
                teacher, _ = Teacher.objects.get_or_create(admin__full_name=teacher_name)

            # Create or update ClassSchedule
            ClassSchedule.objects.get_or_create(
                course=course,
                teacher=teacher,
                day=safe_get(row, '星期', 0),
                start_time=safe_get(row, '开始时间', '08:00'),
                defaults={
                    'grade': safe_get(row, '年级', 1),
                    'end_time': safe_get(row, '结束时间', '10:00'),
                    'lesson_hours': safe_get(row, '课时', 2),
                    'remark': safe_get(row, '备注', ''),
                }
            )

            print(f"ClassSchedule instance saved or updated for course: {course_name}")

        except Course.DoesNotExist:
            print(f"Course {course_name} does not exist.")
        except Exception as e:
            print(f"Exception: {e}")
            continue

def process_all_models(excel_file, auto_create_learning_record, auto_create_payment_record):
    # Process each model
    process_data(excel_file, auto_create_learning_record, auto_create_payment_record)
    process_course(excel_file)
    process_class_schedule(excel_file)
    process_learning_record(excel_file)
    process_payment_record(excel_file)
    process_refund_record(excel_file)


def main(excel_file, selected_model, user_type=None, auto_create_learning_record=False, auto_create_payment_record=False):
    if selected_model == 'Mixed':
        process_all_models(excel_file, auto_create_learning_record, auto_create_payment_record)
    elif selected_model == 'CustomUser' and user_type in ['Student', 'Teacher']:
        process_data(excel_file, auto_create_learning_record, auto_create_payment_record, user_type=user_type)
    elif selected_model == 'Course':
        process_course(excel_file)
    elif selected_model == 'LearningRecord':
        process_learning_record(excel_file)
    elif selected_model == 'PaymentRecord':
        process_payment_record(excel_file)
    elif selected_model == 'RefundRecord':
        process_refund_record(excel_file)
    elif selected_model == 'ClassSchedule':
        process_class_schedule(excel_file)
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
            print(f"No model mapping found for sheet: {sheet_name}")

def process_sheet(sheet_name, sheet_data, model_info):
    model = model_info['model']
    field_mapping = model_info['fields']

    for index, row in sheet_data.iterrows():
        data = {}
        for col, field in field_mapping.items():
            data[field] = safe_get(row, col)
        
        try:
            model.objects.update_or_create(**data)
            print(f"{model.__name__} record processed: {data}")
        except IntegrityError as e:
            print(f"IntegrityError for {model.__name__}: {e}")
        except Exception as e:
            print(f"Error for {model.__name__}: {e}")

def fake_value(column_name):
    fake = Faker()
    if column_name == '出生日期':
        return fake.date_of_birth(minimum_age=10, maximum_age=18).isoformat()
    elif column_name == '注册日期':
        return fake.date_this_year().isoformat()
    elif column_name == '状态':
        return 'Currently Learning'
    # Add more cases for other columns as needed
    return fake.word()
