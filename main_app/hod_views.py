import io
import json
import requests
import pandas as pd
import logging
import pytz
import uuid

from django.core.paginator import Paginator
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponse, HttpResponseRedirect,
                              get_object_or_404, redirect, render)
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import UpdateView
from django.db.models import Sum, F
from django.contrib.auth.hashers import make_password
from django.shortcuts import render
from generate import generate_html_table, process_data
from .forms import *
from .models import *
from .forms import ExcelUploadForm
from django.utils.translation import gettext as _
from django.views.generic import TemplateView
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import JsonResponse
from django.core import serializers
from dateutil.relativedelta import relativedelta
from django.shortcuts import render
from django.utils.translation import gettext as _
from django.db.models import Sum, Count
from django.utils import timezone



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

#Get and Fetch Functions
def get_grade_choices(request):
    course_id = request.GET.get('course_id')
    if course_id:
        choices = ClassScheduleForm().get_level_grade_choices(course_id)
    else:
        choices = []
    return JsonResponse({'choices': choices})

def get_upload(request):
    is_chinese_data = True  # Manually set this flag to True if the data is Chinese

    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            is_teacher = form.cleaned_data['is_teacher']
            try:
                # Process the uploaded Excel file
                processed_data = process_data(excel_file, is_teacher, is_chinese_data)
                html_table = get_result(excel_file, is_teacher)
                message = 'Data processed successfully!'
                context = {'message': message, 'processed_data': processed_data, 'html_table': html_table}
            except Exception as e:
                message = f"Failed to process data: {str(e)}"
                context = {'message': message}
            return render(request, 'hod_template/result.html', context)
    else:
        form = ExcelUploadForm()
    return render(request, 'hod_template/upload.html', {'form': form})

def get_result(excel_file, is_teacher):
    # Read the Excel file into a DataFrame
    df = pd.read_excel(excel_file.file)
    # Convert DataFrame to HTML table
    html_table = df.to_html(index=False, classes='table table-bordered table-striped')
    return html_table

def get_total_income_by_months(start_year, end_year, start_month_name, end_month_name):
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
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            # Skip months outside the specified range in the first and last year
            if (year == start_year and month < start_month) or (year == end_year and month > end_month):
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

def fetch_class_schedule(request):
    course_id = request.GET.get('course_id')
    teacher_id = request.GET.get('teacher_id')
    
    form = LearningRecordForm()
    data = form.fetch_class_schedule_data(course_id, teacher_id)
    
    return JsonResponse(data)

def filter_teachers(request):
    course_id = request.GET.get('course_id')
    form = LearningRecordForm()
    teachers_data = form.fetch_teacher_data(course_id)
    # print(teachers_data)
    return JsonResponse({'teachers': teachers_data})

    
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

        payment_info = {
            'student_name': student_record.admin.full_name if student_record and student_record.admin else 'Unknown',
            'date_of_birth': student_record.date_of_birth if student_record else 'Unknown',
            'course': learning_record.course if learning_record else 'Unknown',
            'total_hours': payment_record.lesson_hours if payment_record.lesson_hours is not None else 'Unknown',
            'hours_spent': student_query.completed_hours if student_query and student_query.completed_hours is not None else 'Unknown',
            'hours_remaining': student_query.remaining_hours if student_query and student_query.remaining_hours is not None else 'Unknown',
            'lesson_price': payment_record.lesson_unit_price if payment_record.lesson_unit_price is not None else 'Unknown',
            'refund_amount': payment_record.amount_paid if payment_record.amount_paid is not None else 'Unknown',
            'amount_refunded': (
                (payment_record.amount_paid - payment_record.lesson_unit_price) +
                ((payment_record.lesson_unit_price / payment_record.lesson_hours) * student_query.remaining_hours)
            ) if all([
                payment_record.amount_paid is not None,
                payment_record.lesson_unit_price is not None,
                payment_record.lesson_hours is not None,
                student_query and student_query.remaining_hours is not None
            ]) else 'Unknown',
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

#Admin
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
        students_count = Student.objects.filter(course_id=course.pk).count()
        course_name_list.append(course.name)
        student_count_list_in_course.append(students_count)

    # Attendance rate for each class schedule
    attendance_rate_list = []
    class_schedule_names_list = []
    for class_obj in classes:
        total_students_in_class = Attendance.objects.filter(classes=class_obj).count()
        total_attendance_in_class = AttendanceReport.objects.filter(attendance__classes=class_obj, status=True).count()
        if total_students_in_class > 0:
            attendance_rate = (total_attendance_in_class / total_students_in_class) * 100
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
        lesson_hours.append(total_hours)

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
        start_year = session.start_year.year
        end_year = session.end_year.year
        available_years.update(range(start_year, end_year + 1))
        monthly_income = get_total_income_by_months(start_year, end_year, "January", "December")
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

#Sessions
def add_session(request):
    form = SessionForm(request.POST or None)
    context = {'form': form, 'page_title': _('Add Session')}
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Session Created")
                return redirect(reverse('add_session'))
            except Exception as e:
                messages.error(request, 'Could Not Add ' + str(e))
        else:
            messages.error(request, 'Fill Form Properly ')
    return render(request, "hod_template/add_session_template.html", context)

def edit_session(request, session_id):
    instance = get_object_or_404(Session, id=session_id)
    form = SessionForm(request.POST or None, instance=instance)
    context = {'form': form, 'session_id': session_id,
               'page_title': 'Edit Session'}
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Session Updated")
                return redirect(reverse('edit_session', args=[session_id]))
            except Exception as e:
                messages.error(
                    request, "Session Could Not Be Updated " + str(e))
                return render(request, "hod_template/edit_session_template.html", context)
        else:
            messages.error(request, "Invalid Form Submitted ")
            return render(request, "hod_template/edit_session_template.html", context)

    else:
        return render(request, "hod_template/edit_session_template.html", context)
    
def delete_session(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    try:
        session.delete()
        messages.success(request, "Session deleted successfully!")
    except Exception:
        messages.error(
            request, "There are students assigned to this session. Please move them to another session.")
    return redirect(reverse('manage_session'))

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
            # institution = form.cleaned_data.get('institution')
            campus = form.cleaned_data.get('campus')
            remark = form.cleaned_data.get('remark')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password')
            course = form.cleaned_data.get('course')
            work_type = form.cleaned_data.get('work_type')
            # passport = request.FILES.get('profile_pic')
            # fs = FileSystemStorage()
            # filename = fs.save(passport.name, passport)
            # passport_url = fs.url(filename)
            try:
                user = CustomUser.objects.create_user(
                    email=email, password=password, user_type=2, full_name=full_name, profile_pic=None)
                user.gender = gender
                user.email = email
                user.address = address
                user.phone_number = phone_number
                # user.teacher.institution = institution
                user.teacher.campus = campus
                user.remark = remark
                user.teacher.course = course
                user.teacher.work_type = work_type
                user.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_teacher'))

            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Please fulfil all requirements")

    return render(request, 'hod_template/add_teacher_template.html', context)

def edit_teacher(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    form = TeacherForm(request.POST or None, instance=teacher)
    context = {
        'form': form,
        'teacher_id': teacher_id,
        'page_title': _('Edit teacher')
    }

    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_teacher', args=[teacher_id]))
            except Exception as e:
                messages.error(request, "Could Not Update: " + str(e))
        else:
            messages.error(request, "Please fill the form properly")

    return render(request, "hod_template/edit_teacher_template.html", context)

def delete_teacher(request, teacher_id):
    teacher = get_object_or_404(CustomUser, teacher__id=teacher_id)
    teacher.delete()
    messages.success(request, "teacher deleted successfully!")
    return redirect(reverse('manage_teacher'))

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
    # Get all teachers
    teachers = CustomUser.objects.filter(user_type=2)

    # Get the selected teacher ID from the form submission
    selected_teacher_id = request.GET.get('teacher_id')

    # Initialize the teacher_query_info list outside the if block
    teacher_query_info = []

    # If a teacher is selected, filter teacher queries by that teacher
    if selected_teacher_id:
        # Retrieve the selected teacher's queries
        teacher_queries = TeacherQuery.objects.filter(admin_id=selected_teacher_id)

        # Iterate over each teacher query
        for teacher_query in teacher_queries:
            # Safely get related teacher information with fallback values
            learning_record = teacher_query.learning_records
            teacher_info = {
                'teacher_name': teacher_query.admin.full_name if teacher_query.teacher_records and teacher_query.teacher_records.admin else 'Unknown',
                'gender': teacher_query.admin.gender if teacher_query.admin else 'Unknown',
                'phone_number': teacher_query.teacher_records.admin.phone_number if teacher_query.teacher_records and teacher_query.teacher_records.admin else 'Unknown',
                'campus': teacher_query.teacher_records.campus if teacher_query.teacher_records else 'Unknown',
                'address': teacher_query.teacher_records.admin.address if teacher_query.teacher_records and teacher_query.teacher_records.admin else 'Unknown',
                'num_of_classes': teacher_query.num_of_classes if teacher_query.num_of_classes is not None else 'Unknown',
                'contract': teacher_query.teacher_records.work_type if teacher_query.teacher_records else 'Unknown',
                'completed_hours': teacher_query.completed_hours if teacher_query.completed_hours is not None else 'Unknown',
                'remaining_hours': teacher_query.remaining_hours if teacher_query.remaining_hours is not None else 'Unknown',
                'date': learning_record.date if learning_record else 'Unknown',
                'course': learning_record.course if learning_record else 'Unknown',
                'instructor': learning_record.teacher if learning_record else 'Unknown',
                'start_time': learning_record.start_time if learning_record else 'Unknown',
                'end_time': learning_record.end_time if learning_record else 'Unknown',
                'lesson_hours': learning_record.lesson_hours if learning_record else 'Unknown',
                # 'class': learning_record.class_name if learning_record else None,
            }
            # Append teacher query information to the list
            teacher_query_info.append(teacher_info)

    # Prepare the context to pass to the template
    context = {
        'teachers': teachers,
        'teacher_query_info': teacher_query_info,
        'page_title': 'Manage Teacher Queries'
    }

    # Render the template with the context
    return render(request, 'hod_template/manage_teacher_query.html', context)



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
            
            # Generate a unique placeholder email if none is provided
            email = form.cleaned_data.get('email')
            if not email:
                unique_id = uuid.uuid4()
                email = f"{full_name.replace(' ', '').lower()}_{unique_id}@placeholder.com"

            try:
                user = CustomUser.objects.create_user(
                    email=email, password=password, user_type=3, full_name=full_name, profile_pic=None)
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
              
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_student'))
            except Exception as e:
                messages.error(request, "Could Not Add: " + str(e))
        else:
            messages.error(request, "Could Not Add: ")
    return render(request, 'hod_template/add_student_template.html', context)

def edit_student(request, student_id):
    student = get_object_or_404(Student, admin=student_id)
    form = StudentForm(request.POST or None, instance=student)
    context = {
        'form': form,
        'student_id': student_id,
        'page_title': _('Edit Student')
    }

    if request.method == 'POST':
        if form.is_valid():
            cleaned_data = form.cleaned_data
            full_name = cleaned_data.get('full_name')
            grade = cleaned_data.get('grade')
            phone_number = cleaned_data.get('phone_number')
            address = cleaned_data.get('address')
            gender = cleaned_data.get('gender')
            password = cleaned_data.get('password') or None
            status = cleaned_data.get('status')
            remark = cleaned_data.get('remark')
            campus = form.cleaned_data.get('campus')

            try:
                user = student.admin
                # user.email = email

                if password is not None:
                    user.set_password(password)

                # if passport is not None:
                #     fs = FileSystemStorage()
                #     filename = fs.save(passport.name, passport)
                #     passport_url = fs.url(filename)
                #     user.profile_pic = passport_url

                user.phone_number = phone_number
                user.full_name = full_name
                user.gender = gender
                user.address = address
                user.remark = remark

                student.status = status
                student.grade = grade
                student.campus = campus
           
                user.save()
                student.save()

                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_student', args=[student_id]))
            except Exception as e:
                messages.error(request, "Could Not Update: " + str(e))
        else:
            messages.error(request, "Please fill the form properly")
    else:
        return render(request, "hod_template/edit_student_template.html", context)

    return render(request, "hod_template/edit_student_template.html", context)

def delete_student(request, student_id):
    student = get_object_or_404(CustomUser, id=student_id)
    student.delete()
    messages.success(request, "Student deleted successfully!")
    return redirect(reverse('manage_student'))

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

def manage_student_query(request):
    # Get all students
    students = CustomUser.objects.filter(user_type=3)

    # Get the selected student ID from the form submission
    selected_student_id = request.GET.get('student_id')

    # Initialize the student_query_info list outside the if block
    student_query_info = []

    # If a student is selected, filter student queries by that student
    if selected_student_id:
        try:
            # Retrieve the selected student's queries and related objects
            student_queries = StudentQuery.objects.filter(student_records__admin__id=selected_student_id).select_related(
                'student_records__admin', 'payment_records', 'learning_records'
            )
            # print(f"Student Queries: {student_queries}")

            # Iterate over each student query
            for student_query in student_queries:
                # Check if the student_query has an associated payment_records object
                if student_query.payment_records:
                    priceper = (student_query.payment_records.amount_paid / student_query.payment_records.lesson_hours) if student_query.payment_records.lesson_hours else 0

                    # Safely get related student information with fallback values
                    student_info = {
                        'student_name': student_query.student_records.admin.full_name if student_query.student_records and student_query.student_records.admin else 'Unknown',
                        'gender': student_query.student_records.admin.gender if student_query.student_records and student_query.student_records.admin else 'Unknown',
                        'date_of_birth': student_query.student_records.date_of_birth if student_query.student_records else 'Unknown',
                        'phone_number': student_query.student_records.admin.phone_number if student_query.student_records and student_query.student_records.admin else 'Unknown',
                        'campus': student_query.student_records.campus if student_query.student_records else 'Unknown',
                        'state': student_query.student_records.status if student_query.student_records else 'Unknown',
                        'payment_status': student_query.payment_records.status if student_query.payment_records else 'Unknown',
                        'refunded': student_query.refund if student_query.refund is not None else 'Unknown',
                        'reg_date': student_query.student_records.reg_date if student_query.student_records else 'Unknown',
                        'num_of_classes': student_query.num_of_classes if student_query.num_of_classes is not None else 'Unknown',
                        'registered_courses': student_query.registered_courses if student_query.registered_courses else 'Unknown',
                        'completed_hours': student_query.completed_hours if student_query.completed_hours is not None else 'Unknown',
                        'remaining_hours': student_query.remaining_hours if student_query.remaining_hours is not None else 'Unknown',
                        'date': student_query.learning_records.date if student_query.learning_records else 'Unknown',
                        'course': student_query.learning_records.course if student_query.learning_records else 'Unknown',
                        'instructor': student_query.learning_records.teacher if student_query.learning_records else 'Unknown',
                        'start_time': student_query.learning_records.start_time if student_query.learning_records else 'Unknown',
                        'end_time': student_query.learning_records.end_time if student_query.learning_records else 'Unknown',
                        'paid': student_query.payment_records.amount_paid if student_query.payment_records else 'Unknown',
                        'lesson_hours': student_query.learning_records.lesson_hours if student_query.learning_records else 'Unknown',
                        'paid_class_hours': student_query.payment_records.lesson_hours if student_query.payment_records else 'Unknown',
                    }
                    # Append student query information to the list
                    student_query_info.append(student_info)
        except Exception as e:
            logging.error(f"Error retrieving student queries: {e}")
    
    # print(f"Student Query Info: {student_query_info}")

    # Prepare the context to pass to the template
    context = {
        'students': students,
        'student_query_info': student_query_info,
        'page_title': _('Manage Student Queries')
    }

    # Render the template with the context
    return render(request, 'hod_template/manage_student_query.html', context)



#Courses
def add_course(request):
    form = CourseForm(request.POST or None, request.FILES or None)  # Adjusted to include request.FILES
    context = {
        'form': form,
        'page_title': _('Add Course')
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            overview = form.cleaned_data.get('overview')
            level_grade = form.cleaned_data.get('level_grade')
            image = form.cleaned_data.get('image')  # Get the image from cleaned_data
            try:
                course = Course()
                course.name = name
                course.overview = overview
                course.level_end = level_grade
                course.image = image  # Set the image field
                course.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_course'))
            except Exception as e:
                messages.error(request, f"Could Not Add: {e}")
        else:
            messages.error(request, "Could Not Add")
    return render(request, 'hod_template/add_course_template.html', context)

def edit_course(request, course_id):
    instance = get_object_or_404(Course, id=course_id)
    form = CourseForm(request.POST or None, request.FILES or None, instance=instance)  # Adjusted to include request.FILES
    context = {
        'form': form,
        'course_id': course_id,
        'page_title': _('Edit Course')
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            overview = form.cleaned_data.get('overview')  # corrected field name
            level_grade = form.cleaned_data.get('level_grade')
            image = form.cleaned_data.get('image')  # Get the image from cleaned_data
            try:
                course = Course.objects.get(id=course_id)
                course.name = name
                course.overview = overview
                course.level_end = level_grade
                if image:  # Only update the image if a new one is provided
                    course.image = image
                course.save()
                messages.success(request, "Successfully Updated")
            except Exception as e:
                messages.error(request, f"Could Not Update: {e}")
        else:
            messages.error(request, "Could Not Update")

    return render(request, 'hod_template/edit_course_template.html', context)

def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    try:
        course.delete()
        messages.success(request, "Course deleted successfully!")
    except Exception as e:
        messages.error(request, f"Sorry, some students are assigned to this course already. Kindly change the affected student course and try again. Error: {e}")
    return redirect(reverse('manage_course'))

def manage_course(request):
    courses = Course.objects.all()
    context = {
        'courses': courses,
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
            principal = form.cleaned_data.get('principal')  # New field
            principal_contact_number = form.cleaned_data.get('principal_contact_number')  # New field

            try:
                campus = Campus()
                campus.name = name
                campus.principal = principal  # New field
                campus.principal_contact_number = principal_contact_number  # New field
                campus.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_campus'))
            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Fill Form Properly")

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
            principal = form.cleaned_data.get('principal')  # New field
            principal_contact_number = form.cleaned_data.get('principal_contact_number')  # New field

            try:
                campus = Campus.objects.get(id=campus_id)
                campus.name = name
                campus.principal = principal  # New field
                campus.principal_contact_number = principal_contact_number  # New field
                campus.save()
                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_campus', args=[campus_id]))
            except Exception as e:
                messages.error(request, "Could Not Update " + str(e))
        else:
            messages.error(request, "Fill Form Properly")

    return render(request, 'hod_template/edit_campus_template.html', context)

def delete_campus(request, campus_id):
    campus = get_object_or_404(Campus, id=campus_id)
    campus.delete()
    messages.success(request, "Campus deleted successfully!")
    return redirect(reverse('manage_campus'))

def manage_campus(request):
    campuses = Campus.objects.all()
    context = {
        'campuses': campuses,
        'page_title': _('Manage Campuses')
    }
    return render(request, "hod_template/manage_campus.html", context)


#Payments
def add_payment_record(request):
    form = PaymentRecordForm(request.POST or None)
    context = {
        'form': form,
        'page_title': _('Add Payment Record')
    }
    if request.method == 'POST':
        if form.is_valid():
            date = form.cleaned_data.get('date')
            student = form.cleaned_data.get('student')
            course = form.cleaned_data.get('course')
            learning = form.cleaned_data.get('learning')
            book_costs = form.cleaned_data.get('book_costs')
            other_fee = form.cleaned_data.get('other_fee')
            amount_due = form.cleaned_data.get('amount_due')
            amount_paid = form.cleaned_data.get('amount_paid')
            total_lesson_hours = form.cleaned_data.get('lesson_hours') or 0  # Ensure a default value if not provided
            payment_method = form.cleaned_data.get('payment_method')
            status = form.cleaned_data.get('status')
            payee = form.cleaned_data.get('payee')
            remark = form.cleaned_data.get('remark')

            # Calculate lesson unit price and discounted price
            if total_lesson_hours > 0:
                lesson_unit_price = amount_due / total_lesson_hours
            else:
                lesson_unit_price = 2180

            discounted_price = lesson_unit_price * total_lesson_hours

            try:
                payment = PaymentRecord()
                payment.date = date
                payment.next_payment_date = date + relativedelta(months=1)
                payment.student = student
                payment.course = course
                payment.learning = learning
                payment.lesson_unit_price = lesson_unit_price
                payment.discounted_price = discounted_price
                payment.lesson_hours = total_lesson_hours
                payment.book_costs = book_costs
                payment.other_fee = other_fee
                payment.amount_due = amount_due
                payment.amount_paid = amount_paid
                payment.payment_method = payment_method
                payment.status = status
                payment.payee = payee
                payment.remark = remark
                
                student.course_id = course
                student.save()
                payment.save()
                
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_payment_record'))

            except Exception as e:
                messages.error(request, "Could Not Add: " + str(e))
        else:
            messages.error(request, "Fill Form Properly")

    return render(request, 'hod_template/add_payment_record_template.html', context)

def edit_payment_record(request, payment_id):
    paymentrecord = get_object_or_404(PaymentRecord, id=payment_id)
    form = PaymentRecordForm(request.POST or None, instance=paymentrecord)
    
    context = {
        'form': form,
        'payment_id': payment_id,
        'page_title': _('Edit Payment Record'),
    }
    
    if request.method == 'POST':
        if form.is_valid():
            date = form.cleaned_data.get('date')
            student = form.cleaned_data.get('student')
            course = form.cleaned_data.get('course')
            learning = form.cleaned_data.get('learning')
            book_costs = form.cleaned_data.get('book_costs')
            other_fee = form.cleaned_data.get('other_fee')
            amount_due = form.cleaned_data.get('amount_due')
            amount_paid = form.cleaned_data.get('amount_paid')
            lesson_hours = form.cleaned_data.get('lesson_hours') or 0  # Ensure a default value if not provided
            payment_method = form.cleaned_data.get('payment_method')
            status = form.cleaned_data.get('status')
            payee = form.cleaned_data.get('payee')
            remark = form.cleaned_data.get('remark')

            # Calculate lesson unit price and discounted price
            if lesson_hours > 0:
                lesson_unit_price = amount_due / lesson_hours
            else:
                lesson_unit_price = 2180

            discounted_price = lesson_unit_price * lesson_hours

            try:
                paymentrecord.date = date
                paymentrecord.student = student
                paymentrecord.course = course
                paymentrecord.learning_record = learning
                paymentrecord.lesson_unit_price = lesson_unit_price
                paymentrecord.discounted_price = discounted_price
                paymentrecord.book_costs = book_costs
                paymentrecord.other_fee = other_fee
                paymentrecord.amount_due = amount_due
                paymentrecord.lesson_hours = lesson_hours
                paymentrecord.amount_paid = amount_paid
                paymentrecord.payment_method = payment_method
                paymentrecord.status = status
                paymentrecord.payee = payee
                paymentrecord.remark = remark
                
                student.course_id = course
                student.save()

                paymentrecord.save()

                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_payment_record', args=[payment_id]))
            except Exception as e:
                messages.error(request, "Could Not Update: " + str(e))
        else:
            messages.error(request, "Fill Form Properly")
    return render(request, 'hod_template/edit_payment_record_template.html', context)

def delete_payment_record(request, payment_id):
    payment = get_object_or_404(PaymentRecord, id=payment_id)
    payment.delete()
    messages.success(request, "Record deleted Successfully!")
    return redirect(reverse('manage_payment_record'))

def manage_payment_record(request):
    payments = PaymentRecord.objects.all().select_related('learning_record')
    paginator = Paginator(payments, 10)  # Show 10 records per page

    page_number = request.GET.get('page')
    paginated_payments = paginator.get_page(page_number)

    total_amount_paid = payments.aggregate(Sum('amount_paid'))['amount_paid__sum']

    context = {
        'payments': paginated_payments,
        'total_amount_paid': total_amount_paid if total_amount_paid else 0,
        'page_title': _('Manage Payment Records')
    }
    return render(request, 'hod_template/manage_payment_record.html', context)


#Learning
def add_learning_record(request):
    form = LearningRecordForm(request.POST or None)
    context = {
        'form': form,
        'page_title': _('Add Learning Record')
    }
    if request.method == 'POST':
        if form.is_valid():
            date = form.cleaned_data.get('date')
            student = form.cleaned_data.get('student')
            course = form.cleaned_data.get('course')
            teacher = form.cleaned_data.get('teacher')
            start_time = form.cleaned_data.get('start_time')
            end_time = form.cleaned_data.get('end_time')
            lesson_hours = form.cleaned_data.get('lesson_hours')
            semester = form.cleaned_data.get('semester')
            # Get the remark from the associated student
            remark = student.admin.remark if student and student.admin else None
            
            try:
                learn = LearningRecord()
                learn.date = date
                learn.student = student
                learn.course = course
                learn.teacher = teacher
                learn.start_time = start_time
                learn.end_time = end_time
                learn.lesson_hours = lesson_hours
                learn.semester = semester
                learn.remark = remark  # Assign the remark here
                learn.save()
                
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_learning_record'))

            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Fill Form Properly")

    return render(request, 'hod_template/add_learning_record_template.html', context)

def edit_learning_record(request, learn_id):
    learningrecord = get_object_or_404(LearningRecord, id=learn_id)
    form = LearningRecordForm(request.POST or None, instance=learningrecord)
    context = {
        'form': form,
        'learn_id': learn_id,
        'page_title': _('Edit Learning Record')
    }
    
    if request.method == 'POST':
        if form.is_valid():
            date = form.cleaned_data.get('date')
            student = form.cleaned_data.get('student')
            course = form.cleaned_data.get('course')
            teacher = form.cleaned_data.get('teacher')
            start_time = form.cleaned_data.get('start_time')
            end_time = form.cleaned_data.get('end_time')
            lesson_hours = form.cleaned_data.get('lesson_hours')
            
            try:
                # Check if the course exists
                if not Course.objects.filter(id=course.id).exists():
                    messages.error(request, "Selected course does not exist.")
                    return render(request, 'hod_template/edit_learning_record_template.html', context)
                
                # Update learning record fields
                learningrecord.date = date
                learningrecord.student = student
                learningrecord.course = course
                learningrecord.teacher = teacher
                learningrecord.start_time = start_time
                learningrecord.end_time = end_time
                learningrecord.lesson_hours = lesson_hours
                
                # Get the remark from the associated student
                student.course_id = course
                remark = student.admin.remark if student and student.admin else None
                learningrecord.remark = remark
                student.save()
                learningrecord.save()
              
                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_learning_record', args=[learn_id]))
            except Exception as e:
                messages.error(request, "Could Not Update: " + str(e))
        else:
            messages.error(request, "Fill Form Properly")
            
    return render(request, 'hod_template/edit_learning_record_template.html', context)

def delete_learning_record(request, learn_id):
    learn = get_object_or_404(LearningRecord, id=learn_id)
    learn.delete()
    messages.success(request, "Classes deleted successfully!")
    return redirect(reverse('manage_learning_record'))

def manage_learning_record(request):
    learningrecords = LearningRecord.objects.all()
    teachers = Teacher.objects.all()
    courses = Course.objects.all()

    selected_teacher = request.GET.get('teacher_name', '')
    selected_grade = request.GET.get('grade', '')

    if selected_teacher:
        learningrecords = learningrecords.filter(teacher__admin__id=selected_teacher)
        
    if selected_grade:
        learningrecords = learningrecords.filter(course__level_end=selected_grade)

    paginator = Paginator(learningrecords, 10)  # Show 10 records per page
    page_number = request.GET.get('page')
    paginated_learningrecords = paginator.get_page(page_number)

    # Log the session ID for debugging
    # session_id = request.session.get('session_id', None)
    # logger.debug(f'Session ID: {session_id}')

    context = {
        'learningrecords': paginated_learningrecords,
        'teachers': teachers,
        'grades': [(str(i), chr(64 + i)) for i in range(1, 8)],  # Assuming grades are from 1 to 7
        'selected_teacher': selected_teacher,
        'selected_grade': selected_grade,
        'page_title': _('Manage Learning Records'),
        # 'session_id': session_id  # Add session_id to context
    }

    # Log the entire context for debugging
    # logger.debug(f'Context: {context}')

    return render(request, 'hod_template/manage_learning_record.html', context)


#Schedules
def calculate_lesson_hours(start_time, end_time):
    start = datetime.strptime(start_time.strftime('%H:%M:%S'), '%H:%M:%S')
    end = datetime.strptime(end_time.strftime('%H:%M:%S'), '%H:%M:%S')
    if start_time >= end_time:
        raise ValueError("End time must be after start time.")
    delta = end - start
    hours, remainder = divmod(delta.total_seconds(), 3600)
    minutes, _ = divmod(remainder, 60)
    
    if int(minutes) == 0:
        return f"{int(hours)}h"
    else:
        return f"{int(hours)}h {int(minutes)}m"
    
def add_class_schedule(request):
    form = ClassScheduleForm(request.POST or None)
    context = {
        'form': form,
        'page_title': _('Add Class Schedule')
    }
    if request.method == 'POST':
        if form.is_valid():
            course = form.cleaned_data.get('course')
            lesson_unit_price = form.cleaned_data.get('lesson_unit_price')
            teacher = form.cleaned_data.get('teacher')
            grade = form.cleaned_data.get('grade')
            start_time = form.cleaned_data.get('start_time') 
            end_time = form.cleaned_data.get('end_time') 
            lesson_hours = form.cleaned_data.get('lesson_hours') 
            remark = form.cleaned_data.get('remark')
            
            
            try:
                
                lesson_hours = calculate_lesson_hours(
                    start_time,
                    end_time
                )
                
                class_schedule = ClassSchedule()
                class_schedule.course = course
                class_schedule.lesson_unit_price = lesson_unit_price
                class_schedule.teacher = teacher
                class_schedule.grade = grade
                class_schedule.start_time = start_time
                class_schedule.end_time = end_time
                class_schedule.lesson_hours = lesson_hours
                class_schedule.remark= remark
                class_schedule.save()

                messages.success(request, "Successfully Added")
                return redirect(reverse('add_class_schedule'))

            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Fill Form Properly")

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
            lesson_unit_price = form.cleaned_data.get('lesson_unit_price')
            teacher = form.cleaned_data.get('teacher')
            grade = form.cleaned_data.get('grade')
            start_time = form.cleaned_data.get('start_time') 
            end_time = form.cleaned_data.get('end_time') 
            lesson_hours = form.cleaned_data.get('lesson_hours') 
            remark = form.cleaned_data.get('remark')
            
            
            try:
                lesson_hours = calculate_lesson_hours(
                    start_time,
                    end_time
                )
                
                class_schedule = ClassSchedule.objects.get(id=schedule_id)
                class_schedule.course = course
                class_schedule.lesson_unit_price = lesson_unit_price
                class_schedule.teacher = teacher
                class_schedule.grade = grade
                class_schedule.start_time = start_time
                class_schedule.end_time = end_time
                class_schedule.lesson_hours = lesson_hours
                class_schedule.remark= remark
                class_schedule.save()

                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_class_schedule', args=[schedule_id]))
            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Fill Form Properly")
    return render(request, 'hod_template/edit_class_schedule_template.html', context)

def delete_class_schedule(request, schedule_id):
    schedule = get_object_or_404(ClassSchedule, id=schedule_id)
    schedule.delete()
    messages.success(request, "Class Schedule deleted successfully!")
    return redirect(reverse('manage_class_schedule'))

def manage_class_schedule(request):
    class_schedules = ClassSchedule.objects.all()
    context = {
        'class_schedules': class_schedules,
        'page_title': _('Manage Class Schedule')
    }
    return render(request, "hod_template/manage_class_schedule.html", context)


#Notifications
def admin_notify_teacher(request):
    teachers = CustomUser.objects.filter(user_type=2).select_related('teacher')
    courses = Course.objects.all()
    students = Student.objects.all()
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

# @csrf_exempt
# def student_summary_message(request):
#     if request.method != 'POST':
#         summarys = SummaryStudent.objects.all()
#         context = {
#             'summarys': summarys,
#             'page_title': _('Student Summary Messages')
#         }
#         return render(request, 'hod_template/student_summary_template.html', context)
#     else:
#         summary_id = request.POST.get('id')
#         try:
#             summary = get_object_or_404(SummaryStudent, id=summary_id)
#             reply = request.POST.get('reply')
#             summary.reply = reply
#             summary.save()
#             return HttpResponse(True)
#         except Exception as e:
#             return HttpResponse(False)

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

# @csrf_exempt
# def view_student_leave(request):
#     if request.method != 'POST':
#         allLeave = LeaveReportStudent.objects.all()
#         context = {
#             'allLeave': allLeave,
#             'page_title': _('Leave Applications From Students')
#         }
#         return render(request, "hod_template/student_leave_view.html", context)
#     else:
#         id = request.POST.get('id')
#         status = request.POST.get('status')
#         if (status == '1'):
#             status = 1
#         else:
#             status = -1
#         try:
#             leave = get_object_or_404(LeaveReportStudent, id=id)
#             leave.status = status
#             leave.save()
#             return HttpResponse(True)
#         except Exception as e:
#             return False

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

@csrf_exempt
def send_student_notification(request):
    id = request.POST.get('id')
    message = request.POST.get('message')
    student = get_object_or_404(Student, admin_id=id)
    try:
        url = "https://fcm.googleapis.com/fcm/send"
        body = {
            'notification': {
                'title': "中之学校管理软件",
                'body': message,
                'click_action': reverse('student_view_notification'),
                'icon': static('dist/img/AdminLTELogo.png')
            },
            'to': student.admin.fcm_token
        }
        headers = {'Authorization':
                   'key=AAAA3Bm8j_M:APA91bElZlOLetwV696SoEtgzpJr2qbxBfxVBfDWFiopBWzfCfzQp2nRyC7_A2mlukZEHV4g1AmyC6P_HonvSkY2YyliKt5tT3fe_1lrKod2Daigzhb2xnYQMxUWjCAIQcUexAMPZePB',
                   'Content-Type': 'application/json'}
        data = requests.post(url, data=json.dumps(body), headers=headers)
        notification = NotificationStudent(student=student, message=message)
        notification.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")

# @csrf_exempt
# def send_teacher_notification(request):
#     id = request.POST.get('id')
#     message = request.POST.get('message')
#     teacher = get_object_or_404(Teacher, admin_id=id)
#     try:
#         url = "https://fcm.googleapis.com/fcm/send"
#         body = {
#             'notification': {
#                 'title': "中之学校管理软件",
#                 'body': message,
#                 'click_action': reverse('teacher_view_notification'),
#                 'icon': static('dist/img/AdminLTELogo.png')
#             },
#             'to': teacher.admin.fcm_token
#         }
#         headers = {'Authorization':
#                    'key=AAAA3Bm8j_M:APA91bElZlOLetwV696SoEtgzpJr2qbxBfxVBfDWFiopBWzfCfzQp2nRyC7_A2mlukZEHV4g1AmyC6P_HonvSkY2YyliKt5tT3fe_1lrKod2Daigzhb2xnYQMxUWjCAIQcUexAMPZePB',
#                    'Content-Type': 'application/json'}
#         data = requests.post(url, data=json.dumps(body), headers=headers)

#         # Set the timezone to China Standard Time
#         china_tz = pytz.timezone('Asia/Shanghai')
#         now = timezone.now().astimezone(china_tz)

#         notification = NotificationTeacher(
#             teacher=teacher,
#             message=message,
#             date=now.date(),
#             time=now.time()
#         )
#         notification.save()
#         return HttpResponse("True")
#     except Exception as e:
#         return HttpResponse("False")

@csrf_exempt
def send_teacher_notification(request):
    id = request.POST.get('id')
    message = request.POST.get('message')
    course_id = request.POST.get('course_id')
    teacher = get_object_or_404(Teacher, admin_id=id)
    course = get_object_or_404(Course, id=course_id)
    students = Student.objects.filter(course=course)
    print(course)
    print(students)
    for student in students:
        studentFirst = student
    def calculate_age(birthdate):
        today = datetime.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
        return age

    student_info = "\n".join([f"{studentFirst.admin.full_name} (Age: {calculate_age(studentFirst.date_of_birth)})"])

    detailed_message = f"Course: {course.name}\nStudents:\n{student_info}\n\nMessage: {message}"

    try:
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

        # Set the timezone to China Standard Time
        china_tz = pytz.timezone('Asia/Shanghai')
        now = timezone.now().astimezone(china_tz)

        notification = NotificationTeacher(
            teacher=teacher,
            message=detailed_message,
            course=course,
            student=studentFirst,
            date=now.date(),
            time=now.time()
        )
        notification.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


















