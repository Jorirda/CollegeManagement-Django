# import io
import json
import requests
import pandas as pd
import logging
import pytz
import uuid
from fuzzywuzzy import fuzz, process
from django.core.paginator import Paginator
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponse, HttpResponseRedirect,
                              get_object_or_404, redirect, render)
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
# from django.views.generic import UpdateView
from django.db.models import Sum, F
# from django.contrib.auth.hashers import make_password
from django.shortcuts import render
from generate import  main, process_data
from main_app.model_column_mapping import MODEL_COLUMN_MAPPING
from .forms import *
from .models import *
from .forms import ExcelUploadForm
from django.utils.translation import gettext as _
from django.views.generic import TemplateView
# from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import JsonResponse
# from django.core import serializers
from dateutil.relativedelta import relativedelta
from django.shortcuts import render
from django.utils.translation import gettext as _
from django.db.models import Sum, Count
from django.utils import timezone
from collections import defaultdict
from django.shortcuts import render


import logging
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data_processing.log", encoding='utf-8'),  # Set encoding to 'utf-8'
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SidebarView(TemplateView):
    template_name = 'main_app/sidebar_template.html'

    def get_context_data(self, **kwargs):
        # Get the existing context from the superclass
        context = super().get_context_data(**kwargs)

        # Add user-specific data to the context
        if self.request.user.is_authenticated:
            context['first_name'] = self.request.user.first_name
            context['last_name'] = self.request.user.last_name
        else:
            context['first_name'] = 'Guest'
            context['last_name'] = ''
        return context

#Get Functions
def get_grade_choices(request):
    course_id = request.GET.get('course_id')
    if course_id:
        choices = ClassScheduleForm().get_level_grade_choices(course_id)
    else:
        choices = []
    return JsonResponse({'choices': choices})

# Specific column mapping rules for autofill based on model and user type
SPECIFIC_COLUMN_MAPPING = {
    'CustomUser': {
        'Teacher': {
            '授课老师': '姓名'
        },
        'Student': {
            '学生姓名': '姓名'
        }
    }
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

@csrf_exempt
def check_columns(request):
    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')
        selected_model = request.POST.get('model')
        user_type = request.POST.get('user_type', None)

        if not selected_model:
            return JsonResponse({'success': False, 'error': 'Please select a table type.'})

        try:
            # Read the Excel file into a DataFrame
            df = pd.read_excel(excel_file)

            # Adjust the model based on the user type
            if selected_model == 'CustomUser' and user_type:
                selected_model = user_type

            column_status = {}

            # Check each model's columns
            for model_name, model_info in MODEL_COLUMN_MAPPING.items():
                if model_name == 'CustomUser' or (selected_model == 'CustomUser' and model_name == user_type) or model_name == selected_model:
                    expected_columns = model_info['fields']
                    uploaded_columns = df.columns.tolist()
                    model_column_status = []

                    for col, field in expected_columns.items():
                        col_status = {
                            'name': col,
                            'status': 'exists' if col in uploaded_columns else 'missing',
                            'can_autofill': False,
                            'can_use_fake_data': False
                        }

                        if col_status['status'] == 'missing':
                            # Check specific column mapping rules
                            specific_mapping = SPECIFIC_COLUMN_MAPPING.get('CustomUser', {}).get(user_type, {})
                            if col in specific_mapping.values():
                                for source_col, target_col in specific_mapping.items():
                                    if col == target_col and source_col in uploaded_columns:
                                        col_status['status'] = 'autofill'
                                        col_status['can_autofill'] = True
                                        col_status['autofill_from'] = source_col
                                        break

                            # General autofill logic
                            if not col_status['can_autofill']:
                                for uploaded_col in uploaded_columns:
                                    similarity_ratio = fuzz.ratio(col, uploaded_col)
                                    if similarity_ratio >= 80:
                                        col_status['status'] = 'autofill'
                                        col_status['can_autofill'] = True
                                        col_status['autofill_from'] = uploaded_col
                                        break

                            # Additional logic for 结束级别 autofill
                            if col == '结束级别':
                                col_status['status'] = 'autofill'
                                col_status['can_autofill'] = True

                        if col_status['status'] == 'missing':
                            col_status['can_use_fake_data'] = True

                        model_column_status.append(col_status)

                    column_status[model_name] = model_column_status

            return JsonResponse({'success': True, 'columns': column_status})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_exempt
def get_upload(request):
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            selected_model = form.cleaned_data['model']
            user_type = form.cleaned_data.get('user_type')
            auto_create_learning_record = 'auto_create_learning_record' in request.POST
            auto_create_payment_record = 'auto_create_payment_record' in request.POST

            if selected_model == 'CustomUser' and user_type:
                selected_model = user_type

            try:
                df = pd.read_excel(excel_file)
                print(f"Uploaded columns: {df.columns.tolist()}")
                model_info = MODEL_COLUMN_MAPPING.get(selected_model)
                if not model_info:
                    raise ValueError(f"No model found for the selected type: {selected_model}")

                expected_columns = set(model_info['fields'].keys())
                actual_columns = set(df.columns)
                
                missing_columns = expected_columns - actual_columns
                extra_columns = actual_columns - expected_columns

                # Print columns in English for better debugging
                print(f"Expected columns: {expected_columns}")
                print(f"Actual columns: {actual_columns}")
                print(f"Missing columns: {missing_columns}")
                print(f"Extra columns: {extra_columns}")

                column_status = {col: 'missing' if col in missing_columns else 'extra' if col in extra_columns else 'match' for col in expected_columns}

                # Check required fields
                required_fields = REQUIRED_FIELDS.get(selected_model, [])
                missing_required_fields = [field for field in required_fields if field not in actual_columns]

                for field in missing_required_fields:
                    column_status[field] = 'missing (required)'

                # Handle autofill suggestions
                for col in missing_columns:
                    specific_mapping = SPECIFIC_COLUMN_MAPPING.get(selected_model, {}).get(user_type, {})
                    if col in specific_mapping and specific_mapping[col] in actual_columns:
                        column_status[specific_mapping[col]] = 'autofill'

                # Color coding for columns
                column_colors = {}
                for col, status in column_status.items():
                    if status == 'autofill':
                        column_colors[col] = 'yellow'
                    elif status == 'missing' or status == 'missing (required)':
                        column_colors[col] = 'red'
                    elif status == 'extra':
                        column_colors[col] = 'blue'
                    else:
                        column_colors[col] = 'green'

                context = {
                    'form': form,
                    'column_status': column_status,
                    'column_colors': column_colors,
                    'selected_model': selected_model,
                    'df': df.to_html(index=False)
                }
                main(excel_file, selected_model, user_type, auto_create_learning_record, auto_create_payment_record)  # for uploading to db
                print("Main Ran")
                return render(request, 'hod_template/upload.html', context)

            except Exception as e:
                print(f"Error processing file: {e}")
                context = {'form': form, 'error': str(e)}
                return render(request, 'hod_template/upload.html', context)

    else:
        form = ExcelUploadForm()

    return render(request, 'hod_template/upload.html', {'form': form})

def get_result(excel_file, is_teacher):
    # Read the Excel file into a DataFrame
    df = pd.read_excel(excel_file.file)
    # Convert DataFrame to HTML table
    html_table = df.to_html(index=False, classes='table table-bordered table-striped')
    return html_table

def get_total_income_by_months(start_date, end_date, start_month_name, end_month_name):
    # Dictionary to correlate month names to their numeric values
    month_dict = {
        "January": 1,
        "February": 2,
        "March": 3,
        "April": 4,
        "May": 5,
        "June": 6,
        "July": 7,
        "August": 8,
        "September": 9,
        "October": 10,
        "November": 11,
        "December": 12
    }

    # Convert month names to numeric values using the dictionary
    start_month = month_dict[start_month_name]
    end_month = month_dict[end_month_name]

    # Initialize the result dictionary
    income_by_month = {}

    # Loop through each year and month within the specified range
    for year in range(start_date, end_date + 1):
        for month in range(1, 13):
            # Skip months outside the specified range in the first and last year
            if (year == start_date and month < start_month) or (year == end_date and month > end_month):
                continue
            
            month_name = list(month_dict.keys())[list(month_dict.values()).index(month)]
            month_key = f"{month_name} {year}"

            # Adjust the start date for the current month
            current_start_date = date(year, month, 1)
            
            # Adjust the end date for the current month
            if month == 12:
                current_end_date = date(year, month, 31)
            else:
                current_end_date = date(year, month + 1, 1) - timedelta(days=1)
            
            # Filter payment records that fall within the current month's date range
            total_income = ((PaymentRecord.objects.filter(
                date__gte=current_start_date,
                date__lte=current_end_date
            ).aggregate(total_income=Sum('amount_paid'))['total_income'] or 0))
            
            # Add the result to the dictionary
            income_by_month[month_key] = total_income

    return income_by_month

def get_teachers(request):
    course_id = request.GET.get('course_id')
    print("Course ID:", course_id)  # Add this print statement
    if course_id:
        teachers = Teacher.objects.filter(courses__id=course_id)
        data = {'teachers': [{'id': teacher.id, 'name': teacher.admin.full_name} for teacher in teachers]}
        return JsonResponse(data)
    return JsonResponse({'teachers': []})

def get_schedule(request):
    course_id = request.GET.get('course_id')
    teacher_id = request.GET.get('teacher_id')
    print("Course ID:", course_id)  # Add this print statement
    print("Teacher ID:", teacher_id)  # Add this print statement
    if course_id and teacher_id:
        try:
            schedule = ClassSchedule.objects.get(course_id=course_id, teacher_id=teacher_id)
            data = {
                'schedule': {
                    'day': schedule.get_day_display(),
                    'start_time': schedule.start_time,
                    'end_time': schedule.end_time,
                    'lesson_hours': schedule.lesson_hours,
                }
            }
            return JsonResponse(data)
        except ClassSchedule.DoesNotExist:
            pass
    return JsonResponse({'schedule': None})

def get_classes_taken_by_teachers(request):
    current_month = datetime.now().month
    current_year = datetime.now().year
    teachers = Teacher.objects.all()
    teacher_names = []
    classes_taken = []
    
    for teacher in teachers:
        count = LearningRecord.objects.filter(
            teacher=teacher,
            date__year=current_year,
            date__month=current_month
        ).count()
        teacher_names.append(teacher.full_name)  # Adjust based on your Teacher model
        classes_taken.append(count)
    
    data = {
        'teachers': teacher_names,
        'classes_taken': classes_taken
    }
    return JsonResponse(data)
    
#Refund
def refund_records(request):
    # Fetch all payment records with status 'Refund'
    payment_records = PaymentRecord.objects.filter(status='Refund')

    # Initialize the list to hold payment record information
    payment_record_info = []

    # Iterate over each payment record
    for payment_record in payment_records:
        student_record = payment_record.student
        learning_record = payment_record.learning_record

        # Attempt to find a corresponding StudentQuery record
        student_query = StudentQuery.objects.filter(payment_records=payment_record).first()

        # Fetch the teacher's name correctly
        teacher_name = learning_record.teacher.admin.full_name if learning_record and learning_record.teacher and learning_record.teacher.admin else 'Unknown'

        hours_spent = student_query.completed_hours if student_query and student_query.completed_hours is not None else 'Unknown'
        hours_remaining = student_query.remaining_hours if student_query and student_query.remaining_hours is not None else 'Unknown'
        
        if all([
            payment_record.amount_paid is not None,
            payment_record.lesson_unit_price is not None,
            payment_record.lesson_hours is not None,
            hours_remaining != 'Unknown'
        ]):
            amount_refunded = (payment_record.amount_paid - payment_record.lesson_unit_price) + (
                (payment_record.lesson_unit_price / payment_record.lesson_hours) * hours_remaining
            )
        else:
            amount_refunded = 'Unknown'

        print(f"Payment Record ID: {payment_record.id}")
        print(f"Student Name: {student_record.admin.full_name if student_record and student_record.admin else 'Unknown'}")
        print(f"Hours Spent: {hours_spent}")
        print(f"Hours Remaining: {hours_remaining}")
        print(f"Amount Refunded: {amount_refunded}")

        payment_info = {
            'student_name': student_record.admin.full_name if student_record and student_record.admin else 'Unknown',
            'date_of_birth': student_record.date_of_birth if student_record else 'Unknown',
            'course': learning_record.course if learning_record else 'Unknown',
            'teacher_name': teacher_name,  # Include Teacher Name
            'total_hours': payment_record.lesson_hours if payment_record.lesson_hours is not None else 'Unknown',
            'hours_spent': hours_spent,
            'hours_remaining': hours_remaining,
            'lesson_price': payment_record.lesson_unit_price if payment_record.lesson_unit_price is not None else 'Unknown',
            'refund_amount': payment_record.amount_paid if payment_record.amount_paid is not None else 'Unknown',
            'amount_refunded': amount_refunded,
            'refund_reason': payment_record.remark if payment_record.remark else 'Unknown',
        }
        # Append payment record information to the list
        payment_record_info.append(payment_info)

    # Paginate the payment record information
    paginator = Paginator(payment_record_info, 10)  # Show 10 records per page
    page_number = request.GET.get('page')
    paginated_records = paginator.get_page(page_number)

    context = {
        'refund_info': paginated_records,
        'page_title': _('Manage Refund Records')
    }

    return render(request, 'hod_template/refund_records.html', context)



#Admin
def admin_get_student_attendance(request):
    student_id = request.GET.get('student_id')
    # logger.info(f"Fetching attendance data for student ID: {student_id}")  # Log student ID

    try:
        attendance_reports = AttendanceReport.objects.filter(student_id=student_id).select_related('attendance')
        leave_reports = LeaveReportStudent.objects.filter(student_id=student_id)

        present_count = attendance_reports.filter(status=True).count()
        absent_count = attendance_reports.filter(status=False).count()
        leave_count = leave_reports.count()

        attendance_dates = [report.attendance.date.strftime('%Y-%m-%d') for report in attendance_reports]
        leave_dates = [report.date.strftime('%Y-%m-%d') for report in leave_reports]

        data = {
            'present': present_count,
            'absent': absent_count,
            'leave': leave_count,
            'attendance_dates': attendance_dates,
            'leave_dates': leave_dates,
        }

        logger.info(f"Attendance data: {data}")  # Log the data
        return JsonResponse(data)

    except Exception as e:
        logger.error(f"Error fetching attendance data: {e}")
        return JsonResponse({'error': str(e)}, status=500)

def admin_get_teacher_class_schedules_count(request):
    teacher_id = request.GET.get('teacher_id')
    print(teacher_id)
    class_schedules_count = ClassSchedule.objects.filter(teacher_id=teacher_id).count()
    return JsonResponse({'class_schedules_count': class_schedules_count})

def admin_home(request):
    # Aggregate counts
    total_teacher = Teacher.objects.count()
    total_students = Student.objects.count()
    total_classes = ClassSchedule.objects.count()
    total_course = Course.objects.count()
    total_income = PaymentRecord.objects.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    total_refunds = PaymentRecord.objects.filter(status='Refund').aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0

    # Attendance per class
    classes = ClassSchedule.objects.all()
    attendance_list = []
    classes_list = []
    for class_schedule in classes:
        attendance_count = Attendance.objects.filter(classes=class_schedule).count()
        classes_list.append(class_schedule.course.name[:7])
        attendance_list.append(attendance_count)

    # Students in each course
    course_all = Course.objects.all()
    course_name_list = []
    student_count_list_in_course = []
    for course in course_all:
        students_count = Student.objects.filter(courses=course).count()
        course_name_list.append(course.name)
        student_count_list_in_course.append(students_count)

    # Attendance rate for each class schedule
    attendance_rate_list = []
    class_schedule_names_list = []
    for class_obj in classes:
        total_students_in_class = Attendance.objects.filter(classes=class_obj).count()
        total_attendance_in_class = AttendanceReport.objects.filter(attendance__classes=class_obj, status=True).count()
        if total_students_in_class > 0:
            attendance_rate = (total_attendance_in_class / total_students_in_class) * 1
        else:
            attendance_rate = 0
        class_schedule_names_list.append(class_obj.course.name)
        attendance_rate_list.append(attendance_rate)

    # Student attendance
    student_attendance_present_list = []
    student_attendance_leave_list = []
    student_name_list = []
    student_attendance_rate_list = []
    students = Student.objects.all()
    for student in students:
        attendance = AttendanceReport.objects.filter(student_id=student.id, status=True).count()
        absent = AttendanceReport.objects.filter(student_id=student.id, status=False).count()
        leave = LeaveReportStudent.objects.filter(student_id=student.id, status=1).count()
        total_attendance = attendance + absent + leave
        attendance_rate = (attendance / total_attendance) * 100 if total_attendance > 0 else 0
        student_attendance_present_list.append(attendance)
        student_attendance_leave_list.append(leave + absent)
        student_name_list.append(student.admin.full_name)
        student_attendance_rate_list.append(attendance_rate)

    # Teacher lesson hours
    teacher_names = []
    lesson_hours = []
    for teacher in Teacher.objects.all():
        teacher_names.append(teacher.admin.full_name)
        total_hours = LearningRecord.objects.filter(teacher=teacher).aggregate(Sum('lesson_hours'))['lesson_hours__sum'] or 0
        lesson_hours.append(float(total_hours))  # Convert Decimal to float

    # Monthly income breakdown
    month_dict = {
        "January": 1,
        "February": 2,
        "March": 3,
        "April": 4,
        "May": 5,
        "June": 6,
        "July": 7,
        "August": 8,
        "September": 9,
        "October": 10,
        "November": 11,
        "December": 12
    }
    sessions = Session.objects.all()
    income_by_months = {}
    available_years = set()
    for session in sessions:
        start_date = session.start_date.year
        end_date = session.end_date.year
        available_years.update(range(start_date, end_date + 1))
        monthly_income = get_total_income_by_months(start_date, end_date, "January", "December")
        for month_year, income in monthly_income.items():
            if month_year not in income_by_months:
                income_by_months[month_year] = 0
            income_by_months[month_year] += float(income)  # Convert Decimal to float

    sorted_income_by_months = {k: income_by_months[k] for k in sorted(income_by_months, key=lambda x: (int(x.split()[1]), month_dict[x.split()[0]]))}
    all_months = list(sorted_income_by_months.keys())
    all_incomes = list(sorted_income_by_months.values())

    # Student renewals and withdrawals
    student_renewals = 0
    withdrawal_count = 0
    for student in students:
        payment_records = PaymentRecord.objects.filter(student_id=student.id)
        next_payment_dates = payment_records.values_list('next_payment_date', flat=True).distinct()
        total_semesters = sum(
            payment_records.filter(next_payment_date=next_payment_date).count()
            for next_payment_date in next_payment_dates
        )
        student_renewals += total_semesters
        if student.status == "Refund":
            withdrawal_count += 1

    teachers = Teacher.objects.all()

    context = {
        'page_title': _("Administrative Dashboard"),
        'total_students': total_students,
        'total_teacher': total_teacher,
        'total_course': total_course,
        'total_classes': total_classes,
        'classes_list': json.dumps(classes_list),
        'attendance_list': json.dumps(attendance_list),
        'student_attendance_present_list': json.dumps(student_attendance_present_list),
        'student_attendance_leave_list': json.dumps(student_attendance_leave_list),
        'student_name_list': json.dumps(student_name_list),
        'student_attendance_rate_list': json.dumps(student_attendance_rate_list),
        'attendance_rate_list': json.dumps(attendance_rate_list),
        'class_schedule_names_list': json.dumps(class_schedule_names_list),
        'student_count_list_in_course': json.dumps(student_count_list_in_course),
        'course_name_list': json.dumps(course_name_list),
        'teacher_names': json.dumps(teacher_names),
        'lesson_hours': json.dumps(lesson_hours),
        'total_income': float(total_income),  # Convert Decimal to float
        'total_refunds': float(total_refunds),  # Convert Decimal to float
        'all_months': json.dumps(all_months),
        'all_incomes': json.dumps(all_incomes),
        'available_years': sorted(available_years),
        'student_renewals': student_renewals,
        'withdrawal_count': withdrawal_count,
        'students': students,  # Add students to the context
        'teachers': teachers  # Add teachers to the context
    }

    return render(request, 'hod_template/home_content.html', context)

def admin_view_profile(request):
    admin = get_object_or_404(Admin, admin=request.user)
    form = AdminForm(request.POST or None, request.FILES or None,
                     instance=admin)
    context = {'form': form,
               'page_title': _('View/Edit Profile')
               }
    if request.method == 'POST':
        try:
            if form.is_valid():
                full_name = form.cleaned_data.get('full_name')
                # first_name = form.cleaned_data.get('first_name')
                # last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                passport = request.FILES.get('profile_pic') or None
                custom_user = admin.admin
                if password != None:
                    custom_user.set_password(password)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    custom_user.profile_pic = passport_url
                custom_user.full_name = full_name
                # custom_user.first_name = first_name
                # custom_user.last_name = last_name
                custom_user.save()
                messages.success(request, _("Profile Updated!"))
                return redirect(reverse('admin_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
        except Exception as e:
            messages.error(
                request, "Error Occured While Updating Profile " + str(e))
    return render(request, "hod_template/admin_view_profile.html", context)

def admin_view_attendance(request):
    classes = Course.objects.all()
    sessions = Session.objects.all()
    context = {
        'classes': classes,
        'sessions': sessions,
        'page_title': _('View Attendance')
    }

    return render(request, "hod_template/admin_view_attendance.html", context)

def admin_notify_teacher(request):
    teachers = Teacher.objects.select_related('admin').all()
    courses = Course.objects.all()
    students = Student.objects.select_related('admin').all()
    context = {
        'page_title': "Send Notifications To Teachers",
        'teachers': teachers,
        'courses': courses,
        'students': students,
    }
    return render(request, "hod_template/teacher_notification.html", context)

def admin_notify_student(request):
    student = CustomUser.objects.filter(user_type=3)
    context = {
        'page_title': _("Send Notifications To Students"),
        'students': student
    }
    return render(request, "hod_template/student_notification.html", context)

#Sessions
def add_session(request):
    form = SessionForm(request.POST or None)
    context = {'form': form, 'page_title': _('Add Session')}
    
    if request.method == 'POST' and request.is_ajax():
        if form.is_valid():
            try:
                form.save()
                return JsonResponse({'success': True, 'message': 'Session Created Successfully'})
            except Exception as e:
                return JsonResponse({'success': False, 'message': 'Could Not Add: ' + str(e)}, status=400)
        else:
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'message': 'Fill Form Properly', 'errors': errors}, status=400)

    return render(request, "hod_template/add_session_template.html", context)

def edit_session(request, session_id):
    instance = get_object_or_404(Session, id=session_id)
    form = SessionForm(request.POST or None, instance=instance)
    context = {'form': form, 'session_id': session_id, 'page_title': 'Edit Session'}

    if request.method == 'POST' and request.is_ajax():
        if form.is_valid():
            try:
                form.save()
                return JsonResponse({'success': True, 'message': 'Session Updated Successfully'})
            except Exception as e:
                return JsonResponse({'success': False, 'message': 'Session Could Not Be Updated: ' + str(e)}, status=400)
        else:
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'message': 'Invalid Form Submitted', 'errors': errors}, status=400)

    return render(request, "hod_template/edit_session_template.html", context)
    
def delete_session(request, session_id):
    if request.method == 'POST' and request.is_ajax():
        try:
            session = get_object_or_404(Session, id=session_id)
            session.delete()
            return JsonResponse({'success': True})
        except Session.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Session does not exist'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method or not an AJAX request'})

def manage_session(request):
    sessions = Session.objects.all()
    context = {'sessions': sessions, 'page_title': _('Manage Sessions')}
    return render(request, "hod_template/manage_session.html", context)

#Teachers
def add_teacher(request):
    form = TeacherForm(request.POST or None, request.FILES or None)
    context = {'form': form, 'page_title': _('Add teacher')}
    
    if request.method == 'POST':
        if form.is_valid():
            full_name = form.cleaned_data.get('full_name')
            address = form.cleaned_data.get('address')
            phone_number = form.cleaned_data.get('phone_number')
            campus = form.cleaned_data.get('campus')
            remark = form.cleaned_data.get('remark')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password')
            courses = form.cleaned_data.get('courses')  # Get the courses
            work_type = form.cleaned_data.get('work_type')

            try:
                user = CustomUser.objects.create_user(email=email, password=password, user_type=2, full_name=full_name, profile_pic=None)
                user.gender = gender
                user.address = address
                user.phone_number = phone_number
                user.teacher.campus = campus
                user.remark = remark
                user.teacher.work_type = work_type
                user.save()

                # Set the many-to-many relationship
                user.teacher.courses.set(courses)

                return JsonResponse({'success': True, 'message': 'Teacher Added Successfully'})
            except Exception as e:
                return JsonResponse({'success': False, 'message': 'Could Not Add: ' + str(e)}, status=400)
        else:
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'message': 'Please fulfill all requirements', 'errors': errors}, status=400)

    return render(request, 'hod_template/add_teacher_template.html', context)

def edit_teacher(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    form = TeacherForm(request.POST or None, instance=teacher)
    context = {
        'form': form,
        'teacher_id': teacher_id,
        'page_title': _('Edit teacher')
    }

    if request.method == 'POST' and request.is_ajax():
        if form.is_valid():
            try:
                form.save()
                return JsonResponse({'success': True, 'message': 'Teacher Updated Successfully'})
            except Exception as e:
                return JsonResponse({'success': False, 'message': 'Could Not Update: ' + str(e)}, status=400)
        else:
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'message': 'Please fill the form properly', 'errors': errors}, status=400)

    return render(request, "hod_template/edit_teacher_template.html", context)

def delete_teacher(request, teacher_id):
    if request.method == 'POST' and request.is_ajax():
        try:
            teacher = get_object_or_404(CustomUser, teacher__id=teacher_id)
            teacher.delete()
            return JsonResponse({'success': True})
        except CustomUser.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Teacher does not exist'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method or not an AJAX request'})

def manage_teacher(request):
    allteacher = CustomUser.objects.filter(user_type=2)
    paginator = Paginator(allteacher, 10)  # Show 10 teachers per page

    page_number = request.GET.get('page')
    teachers_page = paginator.get_page(page_number)

    context = {
        'allteacher': teachers_page,
        'total_teacher_count': allteacher.count(),
        'page_title': _('Manage Teachers')
    }
    return render(request, "hod_template/manage_teacher.html", context)

def manage_teacher_query(request):
    teachers = CustomUser.objects.filter(user_type=2)
    selected_teacher_id = request.GET.get('teacher_id')
    teacher_query_info = []

    if selected_teacher_id:
        teacher_queries = TeacherQuery.objects.filter(admin_id=selected_teacher_id)

        for teacher_query in teacher_queries:
            teacher = teacher_query.teacher_records
            if teacher:
                related_learning_records = LearningRecord.objects.filter(teacher=teacher)
                num_of_classes = related_learning_records.count()
                course_info = defaultdict(list)
                teacher_info = {
                    'teacher_name': teacher_query.admin.full_name if teacher_query.admin else 'Unknown',
                    'gender': teacher_query.admin.gender if teacher_query.admin else 'Unknown',
                    'phone_number': teacher_query.admin.phone_number if teacher_query.admin else 'Unknown',
                    'campus': teacher_query.teacher_records.campus if teacher_query.teacher_records else 'Unknown',
                    'address': teacher_query.admin.address if teacher_query.admin else 'Unknown',
                    'num_of_classes': num_of_classes,
                    'contract': teacher_query.teacher_records.work_type if teacher_query.teacher_records else 'Unknown',
                    'completed_hours': teacher_query.completed_hours if teacher_query.completed_hours is not None else 'Unknown',
                    'remaining_hours': teacher_query.remaining_hours if teacher_query.remaining_hours is not None else 'Unknown',
                }

                for course in teacher.courses.all():
                    course_records = related_learning_records.filter(course=course)
                    for record in course_records:
                        course_info[course.name].append({
                            'date': record.date,
                            'course': record.course.name,
                            'instructor': record.teacher.admin.full_name,
                            'start_time': record.start_time,
                            'end_time': record.end_time,
                            'lesson_hours': record.lesson_hours,
                        })

                for course, records in course_info.items():
                    teacher_query_info.append({
                        'course': course,
                        'teacher_name': teacher_info['teacher_name'],
                        'gender': teacher_info['gender'],
                        'phone_number': teacher_info['phone_number'],
                        'campus': teacher_info['campus'],
                        'address': teacher_info['address'],
                        'num_of_classes': teacher_info['num_of_classes'],
                        'contract': teacher_info['contract'],
                        'completed_hours': teacher_info['completed_hours'],
                        'remaining_hours': teacher_info['remaining_hours'],
                        'records': records
                    })

    context = {
        'teachers': teachers,
        'teacher_query_info': teacher_query_info,
        'page_title': 'Manage Teacher Queries'
    }
    return render(request, 'hod_template/manage_teacher_query.html', context)

# def manage_teacher_query(request):
#     teachers = CustomUser.objects.filter(user_type=2)
#     selected_teacher_id = request.GET.get('teacher_id')
#     teacher_query_info = []

#     if selected_teacher_id:
#         teacher_queries = TeacherQuery.objects.filter(admin_id=selected_teacher_id)

#         for teacher_query in teacher_queries:
#             teacher = teacher_query.teacher_records
#             if teacher:
#                 related_learning_records = LearningRecord.objects.filter(teacher=teacher)
#                 for learning_record in related_learning_records:
#                     teacher_info = {
#                         'teacher_name': teacher_query.admin.full_name if teacher_query.teacher_records and teacher_query.teacher_records.admin else 'Unknown',
#                         'gender': teacher_query.admin.gender if teacher_query.admin else 'Unknown',
#                         'phone_number': teacher_query.teacher_records.admin.phone_number if teacher_query.teacher_records and teacher_query.teacher_records.admin else 'Unknown',
#                         'campus': teacher_query.teacher_records.campus if teacher_query.teacher_records else 'Unknown',
#                         'address': teacher_query.teacher_records.admin.address if teacher_query.teacher_records and teacher_query.teacher_records.admin else 'Unknown',
#                         'num_of_classes': teacher_query.num_of_classes if teacher_query.num_of_classes is not None else 'Unknown',
#                         'contract': teacher_query.teacher_records.work_type if teacher_query.teacher_records else 'Unknown',
#                         'completed_hours': teacher_query.completed_hours if teacher_query.completed_hours is not None else 'Unknown',
#                         'remaining_hours': teacher_query.remaining_hours if teacher_query.remaining_hours is not None else 'Unknown',
#                         'date': learning_record.date,
#                         'course': learning_record.course.name,
#                         'instructor': learning_record.teacher.admin.full_name,
#                         'start_time': learning_record.start_time,
#                         'end_time': learning_record.end_time,
#                         'lesson_hours': learning_record.lesson_hours,
#                     }
#                     teacher_query_info.append(teacher_info)

#     context = {
#         'teachers': teachers,
#         'teacher_query_info': teacher_query_info,
#         'page_title': 'Manage Teacher Queries'
#     }
#     return render(request, 'hod_template/manage_teacher_query.html', context)

#Students
def add_student(request):
    form = StudentForm(request.POST or None, request.FILES or None)
    context = {'form': form, 'page_title': _('Add Student')}
    
    if request.method == 'POST':
        if form.is_valid():
            full_name = form.cleaned_data.get('full_name')
            gender = form.cleaned_data.get('gender')
            date_of_birth = form.cleaned_data.get('date_of_birth')
            address = form.cleaned_data.get('address')
            phone_number = form.cleaned_data.get('phone_number')
            password = form.cleaned_data.get('password')
            grade = form.cleaned_data.get('grade')
            reg_date = form.cleaned_data.get('reg_date')
            status = form.cleaned_data.get('status')
            remark = form.cleaned_data.get('remark')
            campus = form.cleaned_data.get('campus')
            courses = form.cleaned_data.get('courses')  # Get courses from form

            try:
                email = form.cleaned_data.get('email') or f"{full_name.replace(' ', '').lower()}_{uuid.uuid4()}@placeholder.com"
                
                user = CustomUser.objects.create_user(email=email, password=password, user_type=3, full_name=full_name, profile_pic=None)
                user.gender = gender
                user.student.date_of_birth = date_of_birth
                user.address = address
                user.phone_number = phone_number
                user.student.status = status
                user.student.grade = grade
                user.student.reg_date = reg_date
                user.remark = remark
                user.student.campus = campus
                user.save()

                # Set the many-to-many relationship
                user.student.courses.set(courses)
              
                return JsonResponse({'success': True, 'message': 'Student Added Successfully'})
            except Exception as e:
                return JsonResponse({'success': False, 'message': 'Could Not Add: ' + str(e)}, status=400)
        else:
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'message': 'Please fulfill all requirements', 'errors': errors}, status=400)

    return render(request, 'hod_template/add_student_template.html', context)

def edit_student(request, student_id):
    student = get_object_or_404(Student, admin_id=student_id)
    form = StudentForm(request.POST or None, instance=student)
    context = {'form': form, 'student_id': student_id, 'page_title': _('Edit Student')}

    if request.method == 'POST' and request.is_ajax():
        if form.is_valid():
            try:
                form.save()
                return JsonResponse({'success': True, 'message': 'Student Updated Successfully'})
            except Exception as e:
                return JsonResponse({'success': False, 'message': 'Could Not Update: ' + str(e)}, status=400)
        else:
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'message': 'Please fill the form properly', 'errors': errors}, status=400)

    return render(request, 'hod_template/edit_student_template.html', context)

def delete_student(request, student_id):
    if request.method == 'POST' and request.is_ajax():
        try:
            student = get_object_or_404(CustomUser, id=student_id)
            student.delete()
            return JsonResponse({'success': True, 'message': 'Student Deleted Successfully!'})
        except CustomUser.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Student does not exist'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method or not an AJAX request'}, status=400)

def manage_student(request):
    students = CustomUser.objects.filter(user_type=3)
    studentextra = Student.objects.filter(admin__user_type=3)
    
    combined_students = []
    for student in students:
        student_extra = studentextra.filter(admin=student).first()
        combined_students.append({
            'id': student.id ,
            'full_name': student.full_name,
            'gender': student.gender,
            'date_of_birth': student_extra.date_of_birth if student_extra else None,
            'address': student.address,
            'phone_number': student.phone_number,
            'reg_date': student_extra.reg_date if student_extra else None,
            'status': student_extra.status if student_extra else None,
            'remark': student.remark if student_extra else None,
            'courses': student_extra.courses.all() if student_extra else None,  # Include courses
        })

    paginator = Paginator(combined_students, 10)  # Show 10 students per page
    page_number = request.GET.get('page')
    students_page = paginator.get_page(page_number)
    
    context = {
        'students': students_page,
        'total_student_count': len(combined_students),
        'page_title': _('Manage Students')
    }
    return render(request, "hod_template/manage_student.html", context)

import logging

logger = logging.getLogger(__name__)

def manage_student_query(request):
    # Get all students
    students = CustomUser.objects.filter(user_type=3)

    # Get the selected student ID from the form submission
    selected_student_id = request.GET.get('student_id')

    # Initialize the student_query_info list
    student_query_info = []

    if selected_student_id:
        try:
            # Retrieve the student record
            student_record = Student.objects.select_related('admin').get(admin__id=selected_student_id)
            student_name = student_record.admin.full_name
            gender = student_record.admin.gender
            date_of_birth = student_record.date_of_birth
            phone_number = student_record.admin.phone_number
            campus = student_record.campus
            state = student_record.status
            reg_date = student_record.reg_date

            # Retrieve payment and learning records
            payment_record = PaymentRecord.objects.filter(student=student_record).first()

            # Ensure lesson_hours are treated as they are
            learning_records = LearningRecord.objects.filter(student=student_record).select_related('course', 'teacher__admin')
            completed_hours = sum(float(record.lesson_hours) for record in learning_records if record.lesson_hours)
            remaining_hours = float(payment_record.lesson_hours) - completed_hours if payment_record and payment_record.lesson_hours else 0

            student_info = {
                'student_name': student_name,
                'gender': gender,
                'date_of_birth': date_of_birth,
                'phone_number': phone_number,
                'campus': campus,
                'state': state,
                'payment_status': payment_record.status if payment_record else 'Unknown',
                'refunded': payment_record.status == 'Refund' if payment_record else 'Unknown',
                'reg_date': reg_date,
                'num_of_classes': learning_records.count(),
                'registered_courses': ", ".join(set(record.course.name for record in learning_records)),
                'completed_hours': completed_hours,
                'remaining_hours': remaining_hours,
                'records': defaultdict(list)
            }

            for record in learning_records:
                course_info = {
                    'date': record.date,
                    'course': record.course.name,
                    'instructor': record.teacher.admin.full_name,
                    'start_time': record.start_time,
                    'end_time': record.end_time,
                    'lesson_hours': record.lesson_hours,
                }
                student_info['records'][record.course.name].append(course_info)

            for course, records in student_info['records'].items():
                student_query_info.append({
                    'course': course,
                    'student_name': student_info['student_name'],
                    'gender': student_info['gender'],
                    'date_of_birth': student_info['date_of_birth'],
                    'phone_number': student_info['phone_number'],
                    'campus': student_info['campus'],
                    'state': student_info['state'],
                    'payment_status': student_info['payment_status'],
                    'refunded': student_info['refunded'],
                    'reg_date': student_info['reg_date'],
                    'num_of_classes': student_info['num_of_classes'],
                    'registered_courses': student_info['registered_courses'],
                    'completed_hours': student_info['completed_hours'],
                    'remaining_hours': student_info['remaining_hours'],
                    'records': records
                })

        except Exception as e:
            logger.error(f"Error retrieving student queries: {e}")

    context = {
        'students': students,
        'student_query_info': student_query_info,
        'page_title': _('Manage Student Queries')
    }

    return render(request, 'hod_template/manage_student_query.html', context)



# def manage_student_query(request):
#     # Get all students
#     students = CustomUser.objects.filter(user_type=3)

#     # Get the selected student ID from the form submission
#     selected_student_id = request.GET.get('student_id')

#     # Initialize the student_query_info list outside the if block
#     student_query_info = []

#     # If a student is selected, filter student queries by that student
#     if selected_student_id:
#         try:
#             # Retrieve the selected student's queries and related objects
#             student_queries = StudentQuery.objects.filter(student_records__admin__id=selected_student_id).select_related(
#                 'student_records__admin', 'payment_records', 'learning_records'
#             )

#             for student_query in student_queries:
#                 if student_query.payment_records:
#                     priceper = (student_query.payment_records.amount_paid / student_query.payment_records.lesson_hours) if student_query.payment_records.lesson_hours else 0

#                     student_info = {
#                         'student_name': student_query.student_records.admin.full_name if student_query.student_records and student_query.student_records.admin else 'Unknown',
#                         'gender': student_query.student_records.admin.gender if student_query.student_records and student_query.student_records.admin else 'Unknown',
#                         'date_of_birth': student_query.student_records.date_of_birth if student_query.student_records else 'Unknown',
#                         'phone_number': student_query.student_records.admin.phone_number if student_query.student_records and student_query.student_records.admin else 'Unknown',
#                         'campus': student_query.student_records.campus if student_query.student_records else 'Unknown',
#                         'state': student_query.student_records.status if student_query.student_records else 'Unknown',
#                         'payment_status': student_query.payment_records.status if student_query.payment_records else 'Unknown',
#                         'refunded': student_query.refund if student_query.refund is not None else 'Unknown',
#                         'reg_date': student_query.student_records.reg_date if student_query.student_records else 'Unknown',
#                         'num_of_classes': student_query.num_of_classes if student_query.num_of_classes is not None else 'Unknown',
#                         'registered_courses': student_query.registered_courses if student_query.registered_courses else 'Unknown',
#                         'completed_hours': student_query.completed_hours if student_query.completed_hours is not None else 'Unknown',
#                         'remaining_hours': student_query.remaining_hours if student_query.remaining_hours is not None else 'Unknown',
#                         'date': student_query.learning_records.date if student_query.learning_records else 'Unknown',
#                         'course': student_query.learning_records.course if student_query.learning_records else 'Unknown',
#                         'instructor': student_query.learning_records.teacher if student_query.learning_records else 'Unknown',
#                         'start_time': student_query.learning_records.start_time if student_query.learning_records else 'Unknown',
#                         'end_time': student_query.learning_records.end_time if student_query.learning_records else 'Unknown',
#                         'paid': student_query.payment_records.amount_paid if student_query.payment_records else 'Unknown',
#                         'lesson_hours': student_query.learning_records.lesson_hours if student_query.learning_records else 'Unknown',
#                         'paid_class_hours': student_query.payment_records.lesson_hours if student_query.payment_records else 'Unknown',
#                     }
#                     student_query_info.append(student_info)
#         except Exception as e:
#             logging.error(f"Error retrieving student queries: {e}")

#     context = {
#         'students': students,
#         'student_query_info': student_query_info,
#         'page_title': _('Manage Student Queries')
#     }

#     return render(request, 'hod_template/manage_student_query.html', context)


#Courses
def add_course(request):
    form = CourseForm(request.POST or None, request.FILES or None)
    context = {'form': form, 'page_title': _('Add Course')}
    
    if request.method == 'POST':
        if form.is_valid():
            # Extract form data
            name = form.cleaned_data.get('name')
            overview = form.cleaned_data.get('overview')
            level_grade = form.cleaned_data.get('level_grade')
            image = form.cleaned_data.get('image')  # Get the image from the form

            try:
                # Create Course instance
                course = Course.objects.create(
                    name=name,
                    overview=overview,
                    level_end=level_grade,
                    image=image  # Set the image field
                )
                return JsonResponse({'success': True, 'message': 'Course Added Successfully'})
            except Exception as e:
                return JsonResponse({'success': False, 'message': 'Could Not Add: ' + str(e)}, status=400)
        else:
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'message': 'Please fulfill all requirements', 'errors': errors}, status=400)
    
    return render(request, 'hod_template/add_course_template.html', context)

def edit_course(request, course_id):
    instance = get_object_or_404(Course, id=course_id)
    form = CourseForm(request.POST or None, request.FILES or None, instance=instance)
    context = {
        'form': form,
        'course_id': course_id,
        'page_title': _('Edit Course')
    }
    if request.method == 'POST':
        if form.is_valid():
            # Extract form data
            name = form.cleaned_data.get('name')
            overview = form.cleaned_data.get('overview')
            level_grade = form.cleaned_data.get('level_grade')
            image = form.cleaned_data.get('image')  # Get the image from the form

            try:
                # Update Course instance
                course = Course.objects.get(id=course_id)
                course.name = name
                course.overview = overview
                course.level_end = level_grade
                course.image = image
                # if image:  # Only update the image if a new one is provided
                #     course.image = image
                course.save()
                return JsonResponse({'success': True, 'message': 'Course Updated Successfully'})
            except Exception as e:
                return JsonResponse({'success': False, 'message': 'Could Not Update: ' + str(e)}, status=400)
        else:
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'message': 'Please fill the form properly', 'errors': errors}, status=400)

    return render(request, 'hod_template/edit_course_template.html', context)

def delete_course(request, course_id):
    if request.method == 'POST' and request.is_ajax():
        try:
            course = get_object_or_404(Course, id=course_id)
            course.delete()
            return JsonResponse({'success': True, 'message': 'Course Deleted Successfully!'})
        except Course.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Course does not exist'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method or not an AJAX request'}, status=400)

def manage_course(request):
    courses = Course.objects.all()
    total_courses = courses.count()  # Calculate the total number of courses
    paginator = Paginator(courses, 10)  # Show 10 courses per page
    page_number = request.GET.get('page')
    courses_page = paginator.get_page(page_number)
    
    context = {
        'courses': courses_page,
        'total_courses': total_courses,  # Pass the total courses to the context
        'page_title': _('Manage Courses')
    }
    return render(request, "hod_template/manage_course.html", context)


#Classes
def add_classes(request):
    form = ClassesForm(request.POST or None)
    context = {
        'form': form,
        'page_title': _('Add Classes')
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            course = form.cleaned_data.get('course')
            teacher = form.cleaned_data.get('teacher')
            try:
                classes = Classes()
                classes.name = name
                classes.teacher = teacher
                classes.course = course
                classes.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_classes'))

            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Fill Form Properly")

    return render(request, 'hod_template/add_classes_template.html', context)

def edit_classes(request, classes_id):
    instance = get_object_or_404(Classes, id=classes_id)
    form = ClassesForm(request.POST or None, instance=instance)
    context = {
        'form': form,
        'classes_id': classes_id,
        'page_title': _('Edit Classes')
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            course = form.cleaned_data.get('course')
            teacher = form.cleaned_data.get('teacher')
            try:
                classes = Classes.objects.get(id=classes_id)
                classes.name = name
                classes.teacher = teacher
                classes.course = course
                classes.save()
                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_classes', args=[classes_id]))
            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Fill Form Properly")
    return render(request, 'hod_template/edit_classes_template.html', context)

def delete_classes(request, classes_id):
    classes = get_object_or_404(Classes, id=classes_id)
    classes.delete()
    messages.success(request, "Classes deleted successfully!")
    return redirect(reverse('manage_classes'))

def manage_classes(request):
    classes = Classes.objects.all()
    context = {
        'classes': classes,
        'page_title': _('Manage Classes')
    }
    return render(request, "hod_template/manage_classes.html", context)

#Campuses
def add_campus(request):
    form = CampusForm(request.POST or None)
    context = {
        'form': form,
        'page_title': _('Add Campus')
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            principal = form.cleaned_data.get('principal')
            principal_contact_number = form.cleaned_data.get('principal_contact_number')

            try:
                campus = Campus()
                campus.name = name
                campus.principal = principal
                campus.principal_contact_number = principal_contact_number
                campus.save()
                return JsonResponse({'success': True, 'message': 'Campus Added Successfully'})
            except Exception as e:
                return JsonResponse({'success': False, 'message': 'Could Not Add: ' + str(e)}, status=400)
        else:
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'message': 'Please fulfill all requirements', 'errors': errors}, status=400)

    return render(request, 'hod_template/add_campus_template.html', context)

def edit_campus(request, campus_id):
    instance = get_object_or_404(Campus, id=campus_id)
    form = CampusForm(request.POST or None, instance=instance)
    context = {
        'form': form,
        'campus_id': campus_id,
        'page_title': _('Edit Campus')
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            principal = form.cleaned_data.get('principal')
            principal_contact_number = form.cleaned_data.get('principal_contact_number')

            try:
                campus = Campus.objects.get(id=campus_id)
                campus.name = name
                campus.principal = principal
                campus.principal_contact_number = principal_contact_number
                campus.save()
                return JsonResponse({'success': True, 'message': 'Campus Updated Successfully'})
            except Exception as e:
                return JsonResponse({'success': False, 'message': 'Could Not Update: ' + str(e)}, status=400)
        else:
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'message': 'Please fulfill all requirements', 'errors': errors}, status=400)

    return render(request, 'hod_template/edit_campus_template.html', context)

def delete_campus(request, campus_id):
    if request.method == 'POST' and request.is_ajax():
        try:
            campus = get_object_or_404(Campus, id=campus_id)
            campus.delete()
            return JsonResponse({'success': True, 'message': 'Campus Deleted Successfully!'})
        except Campus.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Campus does not exist'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method or not an AJAX request'}, status=400)

def manage_campus(request):
    campuses = Campus.objects.all()
    context = {
        'campuses': campuses,
        'page_title': _('Manage Campuses')
    }
    return render(request, "hod_template/manage_campus.html", context)

# Payments
def get_lesson_hours(request):
    student_id = request.GET.get('student_id')
    print(f"Received request for student_id: {student_id}")
    try:
        total_lesson_hours = LearningRecord.objects.filter(student_id=student_id).aggregate(Sum('lesson_hours'))['lesson_hours__sum']
        if total_lesson_hours is None:
            total_lesson_hours = 0
        print(f"Total lesson hours for student {student_id}: {total_lesson_hours}")

        return JsonResponse({'success': True, 'lesson_hours': float(total_lesson_hours)})
    except Exception as e:
        print(f"Error calculating lesson hours for student {student_id}: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

def add_payment_record(request):
    form = PaymentRecordForm(request.POST or None)
    context = {
        'form': form,
        'page_title': _('Add Payment Record')
    }

    if request.method == 'POST' and request.is_ajax():
        if form.is_valid():
            date = form.cleaned_data.get('date')
            student = form.cleaned_data.get('student')
            course = form.cleaned_data.get('course')
            book_costs = form.cleaned_data.get('book_costs')
            other_fee = form.cleaned_data.get('other_fee')
            amount_due = form.cleaned_data.get('amount_due')
            amount_paid = form.cleaned_data.get('amount_paid')
            lesson_hours = form.cleaned_data.get('lesson_hours')  # Added lesson_hours
            payment_method = form.cleaned_data.get('payment_method')
            status = form.cleaned_data.get('status')
            payee = form.cleaned_data.get('payee')
            remark = form.cleaned_data.get('remark')
            next_payment_date = form.cleaned_data.get('next_payment_date')

            # Calculate lesson unit price and discounted price
            if lesson_hours > 0:
                lesson_unit_price = amount_due / lesson_hours
            else:
                lesson_unit_price = 2180

            discounted_price = lesson_unit_price * lesson_hours

            # If next_payment_date is not provided, set it to date + 1 month
            if not next_payment_date:
                next_payment_date = date + relativedelta(months=1)

            try:
                # Create PaymentRecord instance and save it
                payment = PaymentRecord(
                    date=date,
                    next_payment_date=next_payment_date,
                    student=student,
                    course=course,
                    lesson_unit_price=lesson_unit_price,
                    discounted_price=discounted_price,
                    lesson_hours=lesson_hours,  # Added lesson_hours
                    book_costs=book_costs,
                    other_fee=other_fee,
                    amount_due=amount_due,
                    amount_paid=amount_paid,
                    payment_method=payment_method,
                    status=status,
                    payee=payee,
                    remark=remark
                )

                student.course = course
                student.save()
                payment.save()

                # Create corresponding LearningRecord
                learning_record = LearningRecord.objects.create(
                    date=date,
                    student=student,
                    course=course,
                    teacher=course.teacher_set.first(),  # Assuming the course has teachers associated
                    schedule_record=None,  # This can be set appropriately
                    semester=None,  # This can be set appropriately
                    start_time=None,
                    end_time=None,
                    day=date.strftime("%A")  # Assuming day is the day of the week
                )

                # Link the LearningRecord to the PaymentRecord
                payment.learning_record = learning_record
                payment.save()

                return JsonResponse({'success': True, 'message': 'Payment Record Added Successfully'})

            except Exception as e:
                return JsonResponse({'success': False, 'message': 'Could Not Add: ' + str(e)}, status=400)
        else:
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'message': 'Please fulfill all requirements', 'errors': errors}, status=400)

    return render(request, 'hod_template/add_payment_record_template.html', context)

def edit_payment_record(request, payment_id):
    paymentrecord = get_object_or_404(PaymentRecord, id=payment_id)
    form = PaymentRecordForm(request.POST or None, instance=paymentrecord)

    context = {
        'form': form,
        'payment_id': payment_id,
        'page_title': _('Edit Payment Record'),
    }

    if request.method == 'POST' and request.is_ajax():
        if form.is_valid():
            try:
                form.save()
                return JsonResponse({'success': True, 'message': 'Payment Record Updated Successfully'})
            except Exception as e:
                return JsonResponse({'success': False, 'message': 'Could Not Update: ' + str(e)}, status=400)
        else:
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'message': 'Please fill the form properly', 'errors': errors}, status=400)

    return render(request, 'hod_template/edit_payment_record_template.html', context)

def delete_payment_record(request, payment_id):
    if request.method == 'POST' and request.is_ajax():
        try:
            payment = get_object_or_404(PaymentRecord, id=payment_id)
            payment.delete()
            return JsonResponse({'success': True, 'message': 'Payment Record Deleted Successfully!'})
        except PaymentRecord.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Payment record does not exist'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method or not an AJAX request'}, status=400)

def manage_payment_record(request):
    payments = PaymentRecord.objects.all().select_related('learning_record', 'student').order_by('id')
    
    # Calculate total amount paid
    total_amount_paid = payments.aggregate(Sum('amount_paid'))['amount_paid__sum']

    paginator = Paginator(payments, 10)  # Show 10 records per page
    page_number = request.GET.get('page')
    paginated_payments = paginator.get_page(page_number)

    context = {
        'payments': paginated_payments,
        'total_amount_paid': total_amount_paid if total_amount_paid else 0,
        'page_title': _('Manage Payment Records')
    }

    return render(request, 'hod_template/manage_payment_record.html', context)


# Learning
def add_learning_record(request):
    form = LearningRecordForm(request.POST or None)
    context = {'form': form, 'page_title': _('Add Learning Record')}
    
    if request.method == 'POST' and request.is_ajax():
        if form.is_valid():
            try:
                form.save()
                return JsonResponse({'success': True, 'message': 'Successfully Added'})
            except Exception as e:
                return JsonResponse({'success': False, 'message': 'Could Not Add: ' + str(e)}, status=400)
        else:
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'message': 'Please fill the form properly', 'errors': errors}, status=400)
    
    return render(request, 'hod_template/add_learning_record_template.html', context)

def edit_learning_record(request, learn_id):
    learningrecord = get_object_or_404(LearningRecord, id=learn_id)
    form = LearningRecordForm(request.POST or None, instance=learningrecord)
    context = {'form': form, 'learn_id': learn_id, 'page_title': _('Edit Learning Record')}
    
    if request.method == 'POST' and request.is_ajax():
        if form.is_valid():
            try:
                form.save()
                return JsonResponse({'success': True, 'message': 'Successfully Updated'})
            except Exception as e:
                return JsonResponse({'success': False, 'message': 'Could Not Update: ' + str(e)}, status=400)
        else:
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'message': 'Please fill the form properly', 'errors': errors}, status=400)
    
    return render(request, 'hod_template/edit_learning_record_template.html', context)

def delete_learning_record(request, learn_id):
    if request.method == 'POST' and request.is_ajax():
        try:
            learn = get_object_or_404(LearningRecord, id=learn_id)
            learn.delete()
            return JsonResponse({'success': True, 'message': 'Learning Record Deleted Successfully!'})
        except LearningRecord.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Learning record does not exist'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method or not an AJAX request'}, status=400)
    
def manage_learning_record(request):
    # Fetch learning records, teachers, courses, and filter them
    learningrecords = LearningRecord.objects.all().order_by('date', 'student__admin__id')  # Ensure consistent ordering
    teachers = Teacher.objects.all()
    courses = Course.objects.all()
    
    selected_teacher = request.GET.get('teacher_name', '')
    selected_grade = request.GET.get('grade', '')

    if selected_teacher:
        learningrecords = learningrecords.filter(teacher__admin__id=selected_teacher)
        
    if selected_grade:
        learningrecords = learningrecords.filter(course__level_end=selected_grade)

    total_lesson_hours = learningrecords.aggregate(total_hours=Sum('lesson_hours'))['total_hours']

    paginator = Paginator(learningrecords, 10)  # Show 10 records per page
    page_number = request.GET.get('page')
    paginated_learningrecords = paginator.get_page(page_number)

    # New code to fetch day of the week for each learning record
    for learn in learningrecords:
        DAYS_OF_WEEK = {
            0: _('Monday'),
            1: _('Tuesday'),
            2: _('Wednesday'),
            3: _('Thursday'),
            4: _('Friday'),
            5: _('Saturday'),
            6: _('Sunday'),
        }
        # Assuming each learning record has a related ClassSchedule
        day = learn.schedule_record.day if learn.schedule_record else None
        learn.day = DAYS_OF_WEEK.get(day)
        learn.save()
        # print(learn.day)

    context = {
        'learningrecords': paginated_learningrecords,
        'teachers': teachers,
        'grades': [(str(i), chr(64 + i)) for i in range(1, 8)],  # Assuming grades are from 1 to 7
        'selected_teacher': selected_teacher,
        'selected_grade': selected_grade,
        'total_lesson_hours': total_lesson_hours,
        'page_title': _('Manage Learning Records')
    }

    return render(request, 'hod_template/manage_learning_record.html', context)



#Schedules
def calculate_lesson_hours(start_time, end_time):
    start = datetime.combine(datetime.min, start_time)
    end = datetime.combine(datetime.min, end_time)
    if start >= end:
        raise ValueError("End time must be after start time.")
    duration = end - start
    return duration.total_seconds() / 3600  # Convert to hours and return as a decimal value

def add_class_schedule(request):
    form = ClassScheduleForm(request.POST or None)
    context = {
        'form': form,
        'page_title': _('Add Class Schedule')
    }
    if request.method == 'POST':
        if form.is_valid():
            course = form.cleaned_data.get('course')
            teacher = form.cleaned_data.get('teacher')
            grade = form.cleaned_data.get('grade')
            day = form.cleaned_data.get('day')
            start_time = form.cleaned_data.get('start_time')
            end_time = form.cleaned_data.get('end_time')
            remark = form.cleaned_data.get('remark')
            try:
                lesson_hours = calculate_lesson_hours(start_time, end_time)
                class_schedule = ClassSchedule(
                    course=course,
                    teacher=teacher,
                    grade=grade,
                    day=day,
                    start_time=start_time,
                    end_time=end_time,
                    lesson_hours=lesson_hours,
                    remark=remark,
                )
                class_schedule.save()
                return JsonResponse({'success': True, 'message': 'Class Schedule Added Successfully'})
            except Exception as e:
                return JsonResponse({'success': False, 'message': 'Could Not Add: ' + str(e)}, status=400)
        else:
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'message': 'Please fulfill all requirements', 'errors': errors}, status=400)
    return render(request, 'hod_template/add_class_schedule_template.html', context)

def edit_class_schedule(request, schedule_id):
    instance = get_object_or_404(ClassSchedule, id=schedule_id)
    form = ClassScheduleForm(request.POST or None, instance=instance)
    context = {
        'form': form,
        'schedule_id': schedule_id,
        'page_title': _('Edit Class Schedule')
    }
    if request.method == 'POST':
        if form.is_valid():
            course = form.cleaned_data.get('course')
            teacher = form.cleaned_data.get('teacher')
            grade = form.cleaned_data.get('grade')
            day = form.cleaned_data.get('day')
            start_time = form.cleaned_data.get('start_time')
            end_time = form.cleaned_data.get('end_time')
            remark = form.cleaned_data.get('remark')
            try:
                lesson_hours = calculate_lesson_hours(start_time, end_time)
                class_schedule = ClassSchedule(
                    course=course,
                    teacher=teacher,
                    grade=grade,
                    day=day,
                    start_time=start_time,
                    end_time=end_time,
                    lesson_hours=lesson_hours,
                    remark=remark,
                )
                class_schedule.save()
                return JsonResponse({'success': True, 'message': 'Class Schedule Updated Successfully'})
            except Exception as e:
                return JsonResponse({'success': False, 'message': 'Could Not Update: ' + str(e)}, status=400)
        else:
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'message': 'Please fulfill all requirements', 'errors': errors}, status=400)
    return render(request, 'hod_template/edit_class_schedule_template.html', context)

def delete_class_schedule(request, schedule_id):
    if request.method == 'POST' and request.is_ajax():
        try:
            schedule = get_object_or_404(ClassSchedule, id=schedule_id)
            schedule.delete()
            return JsonResponse({'success': True, 'message': 'Class Schedule Deleted Successfully!'})
        except ClassSchedule.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Class schedule does not exist'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method or not an AJAX request'}, status=400)

def manage_class_schedule(request):
    class_schedules = ClassSchedule.objects.all()
    total_class_schedules = class_schedules.count()  # Calculate the total number of class schedules
    
    paginator = Paginator(class_schedules, 10)  # Show 10 class schedules per page
    page_number = request.GET.get('page')
    class_schedules_page = paginator.get_page(page_number)

    context = {
        'class_schedules': class_schedules_page,
        'total_class_schedules': total_class_schedules,  # Pass the total class schedules count to the context
        'page_title': _('Manage Class Schedule')
    }
    return render(request, "hod_template/manage_class_schedule.html", context)



#Notifications
@csrf_exempt
def send_teacher_notification(request):
    try:
        id = request.POST.get('id')
        message = request.POST.get('message')
        course_id = request.POST.get('course_id')
        student_id = request.POST.get('student_id')
        classroom_performance = request.POST.get('classroom_performance')
        status_pictures = request.FILES.get('status_pictures')

        teacher = get_object_or_404(Teacher, admin_id=id)
        course = get_object_or_404(Course, id=course_id)
        student = get_object_or_404(Student, id=student_id)

        # Handle the status picture file if it exists
        notification = NotificationTeacher()
        if status_pictures:
            notification.status_pictures = status_pictures  # Set the image field

        # def calculate_age(birthdate):
        #     if birthdate is None:
        #         return 0
        #     today = timezone.now().date()
        #     age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
        #     return age
        def calculate_age(date_of_birth):
            logger.debug("Calculating age...")
            logger.debug("Date of Birth: %s", date_of_birth)

            if date_of_birth is None:
                logger.debug("Date of Birth is None. Returning age 0.")
                return 0
            
            today = datetime.now().date()
            logger.debug("Today's Date: %s", today)

            age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
            logger.debug("Calculated Age: %s", age)
            
            return age

        student_info = f"{student.admin.full_name} (Age: {calculate_age(student.date_of_birth)})"
        detailed_message = f"Course: {course.name}\nStudent:\n{student_info}\nMessage: {message}"

        china_tz = pytz.timezone('Asia/Shanghai')
        now = timezone.now().astimezone(china_tz)

        notification.teacher = teacher
        notification.message = detailed_message
        notification.course = course
        notification.student = student
        notification.classroom_performance = classroom_performance
        notification.date = now.date()
        notification.time = now.time()
        notification.save()

        url = "https://fcm.googleapis.com/fcm/send"
        body = {
            'notification': {
                'title': "中之学校管理软件",
                'body': detailed_message,
                'click_action': reverse('teacher_view_notification'),
                'icon': static('dist/img/AdminLTELogo.png')
            },
            'to': teacher.admin.fcm_token
        }
        headers = {
            'Authorization': 'key=YOUR_SERVER_KEY',
            'Content-Type': 'application/json'
        }
        data = requests.post(url, data=json.dumps(body), headers=headers)

        return HttpResponse("True")

    except Exception as e:
        print(f"Error while sending notification: {e}")
        return HttpResponse("False")

#Exempts
@csrf_exempt
def check_email_availability(request):
    email = request.POST.get("email")
    try:
        user = CustomUser.objects.filter(email=email).exists()
        if user:
            return HttpResponse(True)
        return HttpResponse(False)
    except Exception as e:
        return HttpResponse(False)


@csrf_exempt
def view_teacher_summary(request):
    if request.method != 'POST':
        summaries = SummaryTeacher.objects.all()
        context = {
            'summaries': summaries,
            'page_title': _('Summaries')
        }
        return render(request, 'hod_template/teacher_summary_template.html', context)
    else:
        summary_id = request.POST.get('id')
        try:
            summary = get_object_or_404(SummaryTeacher, id=summary_id)
            reply = request.POST.get('reply')
            summary.reply = reply
            summary.replied_at = timezone.now()  # Set the reply date
            summary.save()
            return HttpResponse(True)
        except Exception as e:
            return HttpResponse(False)

@csrf_exempt
def delete_teacher_summary(request):
    if request.method == 'POST':
        summary_id = request.POST.get('id')
        try:
            summary = SummaryTeacher.objects.get(pk=summary_id)
            summary.delete()
            return HttpResponse("True")
        except SummaryTeacher.DoesNotExist:
            return HttpResponse("False")
    else:
        return HttpResponse("False")
        
@csrf_exempt
def view_teacher_leave(request):
    if request.method != 'POST':
        allLeave = LeaveReportTeacher.objects.all()
        context = {
            'allLeave': allLeave,
            'page_title': _('Leave Applications From teacher')
        }
        return render(request, "hod_template/teacher_leave_view.html", context)
    else:
        id = request.POST.get('id')
        status = request.POST.get('status')
        if (status == '1'):
            status = 1
        else:
            status = -1
        try:
            leave = get_object_or_404(LeaveReportTeacher, id=id)
            leave.status = status
            leave.save()
            return HttpResponse(True)
        except Exception as e:
            return False


@csrf_exempt
def get_admin_attendance(request):
    classes_id = request.POST.get('classes')
    session_id = request.POST.get('session')
    attendance_date_id = request.POST.get('attendance_date_id')
    # print(attendance_date_id)
    
    try:
        # logger.info(f"Fetching attendance for Class ID: {classes_id}, Session ID: {session_id}, Attendance Date ID: {attendance_date_id}")
        classes = get_object_or_404(ClassSchedule, course=classes_id)
        session = get_object_or_404(Session, id=session_id)
        attendances = Attendance.objects.filter(classes=classes, session=session)
        
        if attendance_date_id:
            attendances = attendances.filter(date=attendance_date_id)

        if not attendances.exists():
            return JsonResponse({'error': _('No attendance records found')}, status=404)

        json_data = []
        for attendance in attendances:
            attendance_reports = AttendanceReport.objects.filter(attendance=attendance)
            for report in attendance_reports:
                data = {
                    "status": str(report.status),
                    "name": str(report.student),
                    "date": str(attendance.date)
                }
                # logger.info(f"Student: {report.student}, Status: {report.status}")
                json_data.append(data)

        return JsonResponse(json.dumps(json_data), safe=False)
    except Exception as e:
        logger.error(f"Error fetching attendance: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def get_attendance_dates(request):
    classes_id = request.POST.get('classes')
    session_id = request.POST.get('session')

    try:
        # logger.info(f"Fetching attendance dates for Class ID: {classes_id}, Session ID: {session_id}")
        classes = get_object_or_404(ClassSchedule, id=classes_id)
        session = get_object_or_404(Session, id=session_id)
        attendance_dates = Attendance.objects.filter(classes=classes, session=session).values('id', 'date')

        json_data = [{"id": attendance['id'], "date": attendance['date'].strftime("%Y-%m-%d")} for attendance in attendance_dates]
        return JsonResponse(json_data, safe=False)
    except Exception as e:
        logger.error(f"Error fetching attendance dates: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

# @csrf_exempt
# def send_student_notification(request):
#     id = request.POST.get('id')
#     message = request.POST.get('message')
#     student = get_object_or_404(Student, admin_id=id)
#     try:
#         url = "https://fcm.googleapis.com/fcm/send"
#         body = {
#             'notification': {
#                 'title': "中之学校管理软件",
#                 'body': message,
#                 'click_action': reverse('student_view_notification'),
#                 'icon': static('dist/img/AdminLTELogo.png')
#             },
#             'to': student.admin.fcm_token
#         }
#         headers = {'Authorization':
#                    'key=AAAA3Bm8j_M:APA91bElZlOLetwV696SoEtgzpJr2qbxBfxVBfDWFiopBWzfCfzQp2nRyC7_A2mlukZEHV4g1AmyC6P_HonvSkY2YyliKt5tT3fe_1lrKod2Daigzhb2xnYQMxUWjCAIQcUexAMPZePB',
#                    'Content-Type': 'application/json'}
#         data = requests.post(url, data=json.dumps(body), headers=headers)
#         notification = NotificationStudent(student=student, message=message)
#         notification.save()
#         return HttpResponse("True")
#     except Exception as e:
#         return HttpResponse("False")