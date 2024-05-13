import io
import json
from django.db import IntegrityError
import requests
import pandas as pd
import numpy as np
import random
import string

from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponse, HttpResponseRedirect,
                              get_object_or_404, redirect, render)
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import UpdateView
from django.db.models import Sum
from django.contrib.auth.hashers import make_password
from django.shortcuts import render
from generate import process_data
from .forms import *
from .models import *
from .forms import ExcelUploadForm
from django.utils.translation import gettext as _
from django.views.generic import TemplateView
from django.core.files.uploadedfile import InMemoryUploadedFile
from datetime import time
from django.http import JsonResponse


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
    
def get_grade_choices(request):
    course_id = request.GET.get('course_id')
    if course_id:
        choices = ClassScheduleForm().get_level_grade_choices(course_id)
    else:
        choices = []
    return JsonResponse({'choices': choices})

def refund_records(request):
    student_query = StudentQuery.objects.all()


    # Initialize a list to hold student query information
    student_query_info = []

    # Iterate over each student query
    for student_query in student_query:
    # Your code here for handling the case where the payment has been refunded

        # Check if the student_query has an associated payment_records object and refund condition is met
        if student_query.payment_records:  # Assuming 'Refunded' is a status
            print(student_query.payment_records.status)
            # Get related student information
            student_info = {
                'student_name': student_query.admin.get_full_name(),
                'date_of_birth': student_query.student_records.date_of_birth,
                'course': student_query.learning_records.course,
                'total_hours' : "student_query.learning_records.total_hours",  # Assuming there's a field for total hours
                'hours_spent': student_query.completed_hours,
                'hours_remaining': student_query.remaining_hours,
                'lesson_price': student_query.payment_records.lesson_unit_price,  # Assuming there's a field for lesson price
                'refund_amount': "?",  # Assuming a function to calculate
                'amount_refunded': student_query.payment_records.amount_paid,  # Assuming this field exists
                'refund_reason': "student_query.refund_reason",  # Assuming this field exists
            }
            # Append student query information to the list
            student_query_info.append(student_info)

    context = {
        'refund_info': student_query_info,
        'page_title': 'Manage Refund Records'
    }

    return render(request, 'hod_template/refund_records.html', context)

def get_upload(request):
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            is_teacher = form.cleaned_data['is_teacher']
            try:

                # Assuming process_excel is the correct function that processes the file
                csv_data = get_result(excel_file, is_teacher)  # Changed from get_upload to process_excel
                process_data(excel_file, is_teacher)
                message = 'Data processed successfully!'
                context = {'message': message, 'html_table': csv_data}
            except Exception as e:
                message = f"Failed to process data: {str(e)}"
                context = {'message': message}
            return render(request, 'hod_template/result.html', context)
    else:
        form = ExcelUploadForm()
    return render(request, 'hod_template/upload.html', {'form': form})

def get_result(excel_file, is_teacher):
    # Assuming excel_file is an InMemoryUploadedFile object from the form
    df = pd.read_excel(excel_file.file)  # Read the Excel file into a DataFrame
    html_table = df.to_html(index=False, classes='table table-bordered table-striped')  # Convert DataFrame to HTML table
    return html_table

def admin_home(request):
    total_teacher = Teacher.objects.all().count()
    total_students = Student.objects.all().count()
    classess = Classes.objects.all()
    total_classes = classess.count()
    total_course = Course.objects.all().count()
    attendance_list = Attendance.objects.filter(classes__in=classess)
    total_attendance = attendance_list.count()
    attendance_list = []
    classes_list = []
    for classes in classess:
        attendance_count = Attendance.objects.filter(classes=classes).count()
        classes_list.append(classes.name[:7])
        attendance_list.append(attendance_count)

    # Total Classess and students in Each Course
    course_all = Course.objects.all()
    course_name_list = []
    classes_count_list = []
    student_count_list_in_course = []

    for course in course_all:
        classess = Classes.objects.filter(course_id=course.id).count()
        students = Student.objects.filter(course_id=course.id).count()
        course_name_list.append(course.name)
        classes_count_list.append(classess)
        student_count_list_in_course.append(students)
    
    classes_all = Classes.objects.all()
    classes_list = []
    student_count_list_in_classes = []
    for classes in classes_all:
        course = Course.objects.get(id=classes.course.id)
        student_count = Student.objects.filter(course_id=course.id).count()
        classes_list.append(classes.name)
        student_count_list_in_classes.append(student_count)


    # For Students
    student_attendance_present_list=[]
    student_attendance_leave_list=[]
    student_name_list=[]

    students = Student.objects.all()
    for student in students:
        
        attendance = AttendanceReport.objects.filter(student_id=student.id, status=True).count()
        absent = AttendanceReport.objects.filter(student_id=student.id, status=False).count()
        leave = LeaveReportStudent.objects.filter(student_id=student.id, status=1).count()
        student_attendance_present_list.append(attendance)
        student_attendance_leave_list.append(leave+absent)
        student_name_list.append(student.admin.first_name)

    context = {
        'page_title': _("Administrative Dashboard"),
        'total_students': total_students,
        'total_teacher': total_teacher,
        'total_course': total_course,
        'total_classes': total_classes,
        'classes_list': classes_list,
        'attendance_list': attendance_list,
        'student_attendance_present_list': student_attendance_present_list,
        'student_attendance_leave_list': student_attendance_leave_list,
        "student_name_list": student_name_list,
        "student_count_list_in_classes": student_count_list_in_classes,
        "student_count_list_in_course": student_count_list_in_course,
        "course_name_list": course_name_list,

    }
    return render(request, 'hod_template/home_content.html', context)

def add_session(request):
    form = SessionForm(request.POST or None)
    context = {'form': form, 'page_title': 'Add Session'}
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
            passport = request.FILES.get('profile_pic')
            fs = FileSystemStorage()
            filename = fs.save(passport.name, passport)
            passport_url = fs.url(filename)
            try:
                user = CustomUser.objects.create_user(
                    email=email, password=password, user_type=2, full_name=full_name, profile_pic=passport_url)
                user.gender = gender
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

def add_student(request):
    form = StudentForm(request.POST or None, request.FILES or None)
    context = {'form': form, 'page_title': _('Add Student')}
    if request.method == 'POST':
        if form.is_valid():
            full_name = form.cleaned_data.get('full_name')
            gender = form.cleaned_data.get('gender')
            date_of_birth = form.cleaned_data.get('date_of_birth')
            address = form.cleaned_data.get('address')
            email = form.cleaned_data.get('email')
            phone_number = form.cleaned_data.get('phone_number')
            password = form.cleaned_data.get('password')
            grade = form.cleaned_data.get('grade')
            reg_date = form.cleaned_data.get('reg_date')
            status = form.cleaned_data.get('status')
            remark = form.cleaned_data.get('remark')
            passport = request.FILES['profile_pic']
            fs = FileSystemStorage()
            filename = fs.save(passport.name, passport)
            passport_url = fs.url(filename)
            try:
                user = CustomUser.objects.create_user(
                    email=email, password=password, user_type=3, full_name=full_name, profile_pic=passport_url)
                user.gender = gender
                user.student.date_of_birth = date_of_birth
                user.address = address
                user.phone_number = phone_number
                user.student.status = status
                user.student.grade = grade
                user.student.reg_date = reg_date
                user.remark = remark
                user.save()
              
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_student'))
            except Exception as e:
                messages.error(request, "Could Not Add: " + str(e))
        else:
            messages.error(request, "Could Not Add: ")
    return render(request, 'hod_template/add_student_template.html', context)

def add_course(request):
    form = CourseForm(request.POST or None)
    context = {
        'form': form,
        'page_title': _('Add Course')
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            overview = form.cleaned_data.get('overview')
            level_grade = form.cleaned_data.get('level_grade')
            try:
                course = Course()
                course.name = name
                course.overview = overview
                course.level_end = level_grade
                course.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_course'))
            except:
                messages.error(request, "Could Not Add")
        else:
            messages.error(request, "Could Not Add")
    return render(request, 'hod_template/add_course_template.html', context)

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

def add_campus(request):
    form = CampusForm(request.POST or None)
    context = {
        'form': form,
        'page_title':  _('Add Campus')
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            # institution = form.cleaned_data.get('institution')
           
         
            try:
                campus = Campus()
                campus.name = name
                # campus.institution = institution
                
            
                campus.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_campus'))

            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Fill Form Properly")

    return render(request, 'hod_template/add_campus_template.html', context)

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
            lesson_unit_price = form.cleaned_data.get('lesson_unit_price')
            discounted_price = form.cleaned_data.get('discounted_price')
            book_costs = form.cleaned_data.get('book_costs')
            other_fee = form.cleaned_data.get('other_fee')
            amount_due = form.cleaned_data.get('amount_due')
            amount_paid = form.cleaned_data.get('amount_paid')
            total_lesson_hours = form.cleaned_data.get('total_lesson_hours')
            payment_method = form.cleaned_data.get('payment_method')
            status = form.cleaned_data.get('status')
            payee = form.cleaned_data.get('payee')
            remark = form.cleaned_data.get('remark')
           
            try:
                payment = PaymentRecord()
                payment.date = date
                payment.student = student
                payment.course = course
                payment.learning = learning
                payment.lesson_unit_price= lesson_unit_price
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
                payment.save()
                
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_payment_record'))

            except Exception as e:
                messages.error(request, "Could Not Add: " + str(e))
        else:
            messages.error(request, "Fill Form Properly")

    return render(request, 'hod_template/add_payment_record_template.html', context)

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
                learn.remark = remark  # Assign the remark here
                learn.save()
                
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_learning_record'))

            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Fill Form Properly")

    return render(request, 'hod_template/add_learning_record_template.html', context)

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

def manage_session(request):
    sessions = Session.objects.all()
    context = {'sessions': sessions, 'page_title': 'Manage Sessions'}
    return render(request, "hod_template/manage_session.html", context)

def manage_teacher(request):
    allteacher = CustomUser.objects.filter(user_type=2)
    total_teacher_count = allteacher.count()
    context = {
        'allteacher': allteacher,
        'total_teacher_count': total_teacher_count,
        'page_title': _('Manage Teachers')
    }
    return render(request, "hod_template/manage_teacher.html", context)

def manage_student(request):
    students = CustomUser.objects.filter(user_type=3)
    total_student_count = students.count()
    context = {
        'students': students,
        'total_student_count':total_student_count,
        'page_title': _('Manage Students')
    }
    return render(request, "hod_template/manage_student.html", context)

def manage_course(request):
    courses = Course.objects.all()
    context = {
        'courses': courses,
        'page_title': _('Manage Courses')
    }
    return render(request, "hod_template/manage_course.html", context)

def manage_classes(request):
    classes = Classes.objects.all()
    context = {
        'classess': classes,
        'page_title': _('Manage Classes')
    }
    return render(request, "hod_template/manage_classes.html", context)

def manage_campus(request):
    campuses = Campus.objects.all()
    context = {
        'campuses': campuses,
        'page_title': _('Manage Campuses')
    }
    return render(request, "hod_template/manage_campus.html", context)

def manage_payment_record(request):
    payments = PaymentRecord.objects.all().select_related('learning_record')
    total_amount_paid = payments.aggregate(Sum('amount_paid'))['amount_paid__sum']
    # for payment in payments:
        # lesson_hours = payment.learning_record.lesson_hours if payment.learning_record else None
        # print(f"Payment ID: {payment.id}, LearningRecord: {lesson_hours}")
    context = {
        'payments': payments,
        'total_amount_paid': total_amount_paid if total_amount_paid else 0,
        'page_title': _('Manage Payment Records')
    }
    return render(request, 'hod_template/manage_payment_record.html', context)

def manage_learning_record(request):
    learningrecords = LearningRecord.objects.all()
    context = {
        'learningrecords': learningrecords,
        'page_title': _('Manage Learning Records')
    }

    return render(request, 'hod_template/manage_learning_record.html', context)

def manage_class_schedule(request):
    class_schedules = ClassSchedule.objects.all()
    context = {
        'class_schedules': class_schedules,
        'page_title': _('Manage Class Schedule')
    }
    return render(request, "hod_template/manage_class_schedule.html", context)

def manage_student_query(request):
    # Get all students
    students = CustomUser.objects.filter(user_type=3)

    # Get the selected student ID from the form submission
    selected_student_id = request.GET.get('student_id')

    # Initialize the student_query_info list outside the if block
    student_query_info = []

    # If a student is selected, filter student queries by that student
    if selected_student_id:
        # Retrieve the selected student's queries
        student_queries = StudentQuery.objects.filter(admin_id=selected_student_id)

        # Iterate over each student query
        for student_query in student_queries:
            # Check if the student_query has an associated payment_records object
            if student_query.payment_records:
                priceper = (student_query.payment_records.amount_paid / student_query.payment_records.lesson_hours)
                # Get related student information
                student_info = {
                    'student_name': student_query.admin.get_full_name(),
                    'gender': student_query.admin.gender,
                    'date_of_birth': student_query.student_records.date_of_birth,
                    'phone_number': student_query.student_records.admin.phone_number,
                    # 'institution': student_query.student_records.institution,
                    'campus': student_query.student_records.campus,
                    # 'grade': student_query.student_records.grade,
                    'state': student_query.student_records.status,
                    'payment_status': student_query.payment_records.status,
                    'refunded': student_query.refund,
                    'reg_date': student_query.student_records.reg_date,
                    'num_of_classes': student_query.num_of_classes,
                    'registered_courses': student_query.registered_courses,
                    'completed_hours': student_query.completed_hours,
                    'remaining_hours': student_query.remaining_hours,
                    'date': student_query.learning_records.date,
                    'course': student_query.learning_records.course,
                    'instructor': student_query.learning_records.teacher,
                    'start_time': student_query.learning_records.start_time,
                    'end_time': student_query.learning_records.end_time,
                    'paid': student_query.payment_records.amount_paid,
                    'lesson_hours': student_query.learning_records.lesson_hours,
                    'paid_class_hours': student_query.payment_records.lesson_hours,
                    # 'class': student_query.learning_records.class_name,
                }
                # Append student query information to the list
                student_query_info.append(student_info)



    # Prepare the context to pass to the template
    context = {
        'students': students,
        'student_query_info': student_query_info,
        'page_title': _('Manage Student Queries')
    }

    # Render the template with the context
    return render(request, 'hod_template/manage_student_query.html', context)

def manage_teacher_query(request):
    # Get all teachers
    teachers = CustomUser.objects.filter(user_type=2)

    # Get the selected teacher ID from the form submission
    selected_teacher_id = request.GET.get('teacher_id')

    # Initialize teacher_query_info list
    teacher_query_info = []

    # If a teacher is selected, filter teacher queries by that teacher
    if selected_teacher_id:
        # Retrieve the selected teacher's queries
        teacher_queries = TeacherQuery.objects.filter(admin_id=selected_teacher_id)

        # Iterate over each teacher query
        for teacher_query in teacher_queries:
            # Get related teacher information
            teacher_info = {
                'teacher_name': teacher_query.admin.get_full_name(),
                'gender': teacher_query.admin.gender,
                'phone_number': teacher_query.teacher_records.admin.phone_number,
                'campus': teacher_query.teacher_records.campus,
                'address': teacher_query.teacher_records.admin.address,
                'num_of_classes': teacher_query.num_of_classes,
                'contract': teacher_query.teacher_records.work_type,
                'completed_hours': teacher_query.completed_hours,
                'remaining_hours': teacher_query.remaining_hours,
                'date': teacher_query.learning_records.date if teacher_query.learning_records else None,
                'course': teacher_query.learning_records.course if teacher_query.learning_records else None,
                'instructor': teacher_query.learning_records.teacher if teacher_query.learning_records else None,
                'start_time': teacher_query.learning_records.start_time if teacher_query.learning_records else None,
                'end_time': teacher_query.learning_records.end_time if teacher_query.learning_records else None,
                # 'class': teacher_query.learning_records.class_name if teacher_query.learning_records else None,
            }
            # Append teacher query information to the list
            teacher_query_info.append(teacher_info)
    else:
        # If no teacher is selected, retrieve all teacher queries
        # Iterate over each teacher query
        for teacher_query in TeacherQuery.objects.all():
            # Get related teacher information
            teacher_info = {
                'teacher_name': teacher_query.admin.get_full_name(),
                'gender': teacher_query.admin.gender,
                'phone_number': teacher_query.teacher_records.admin.phone_number,
                'campus': teacher_query.teacher_records.campus,
                'address': teacher_query.teacher_records.admin.address,
                'num_of_classes': teacher_query.num_of_classes,
                'contract': teacher_query.teacher_records.work_type,
                'completed_hours': teacher_query.completed_hours,
                'remaining_hours': teacher_query.remaining_hours,
                'date': teacher_query.learning_records.date if teacher_query.learning_records else None,
                'course': teacher_query.learning_records.course if teacher_query.learning_records else None,
                'instructor': teacher_query.learning_records.teacher if teacher_query.learning_records else None,
                'start_time': teacher_query.learning_records.start_time if teacher_query.learning_records else None,
                'end_time': teacher_query.learning_records.end_time if teacher_query.learning_records else None,
                # 'class': teacher_query.learning_records.class_name if teacher_query.learning_records else None,
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
            # Extract cleaned data from the form
            cleaned_data = form.cleaned_data

            # Extract required data
            full_name = cleaned_data.get('full_name')
            # email = cleaned_data.get('email')
            gender = cleaned_data.get('gender')
            password = cleaned_data.get('password') or None
            address = cleaned_data.get('address')  # Extract address here
            phone_number = cleaned_data.get('phone_number')
            # institution = cleaned_data.get('institution')
            campus = cleaned_data.get('campus')
            course = cleaned_data.get('course')
            work_type = cleaned_data.get('work_type')
            remark = cleaned_data.get('remark')
            # passport = request.FILES.get('profile_pic')

            try:
                # Get the related CustomUser object directly from the teacher's admin attribute
                user = teacher.admin
                # user.email = email
                user.remark = remark
                user.full_name = full_name
                user.gender = gender
                user.address = address  # Set the address here
                user.phone_number = phone_number

                # If password is provided, set it
                if password is not None:
                    user.set_password(password)

                # If profile pic is provided, save it
                # if passport is not None:
                #     fs = FileSystemStorage()
                #     filename = fs.save(passport.name, passport)
                #     passport_url = fs.url(filename)
                #     user.profile_pic = passport_url

                # Update teacher details 
                # teacher.institution = institution
                teacher.campus = campus
                teacher.course = course
                teacher.work_type = work_type
              
                # Save changes
                user.save()
                teacher.save()

                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_teacher', args=[teacher_id]))
            except Exception as e:
                messages.error(request, "Could Not Update: " + str(e))
        else:
            messages.error(request, "Please fill the form properly")
    else:
        # For GET request, render the form template
        return render(request, "hod_template/edit_teacher_template.html", context)

    # If the request is POST or if there's an error, render the form template with errors
    return render(request, "hod_template/edit_teacher_template.html", context)

def edit_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
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

def edit_course(request, course_id):
    instance = get_object_or_404(Course, id=course_id)
    form = CourseForm(request.POST or None, instance=instance)
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
            try:
                course = Course.objects.get(id=course_id)
                course.name = name
                course.overview = overview
                course.level_end = level_grade
                course.save()
                messages.success(request, "Successfully Updated")
            except:
                messages.error(request, "Could Not Update")
        else:
            messages.error(request, "Could Not Update")

    return render(request, 'hod_template/edit_course_template.html', context)

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
            # institution = form.cleaned_data.get('institution')
           
           
            try:
                campus = Campus.objects.get(id=campus_id)
                campus.name = name
                # campus.institution = institution
              
               
                campus.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('edit_campus', args=[campus_id]))

            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Fill Form Properly")

    return render(request, 'hod_template/edit_campus_template.html', context)

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
            lesson_unit_price = form.cleaned_data.get('lesson_unit_price')
            discounted_price = form.cleaned_data.get('discounted_price')
            book_costs = form.cleaned_data.get('book_costs')
            other_fee = form.cleaned_data.get('other_fee')
            amount_due = form.cleaned_data.get('amount_due')
            amount_paid = form.cleaned_data.get('amount_paid')
            lesson_hours = form.cleaned_data.get('lesson_hours')
            print(lesson_hours)
            payment_method = form.cleaned_data.get('payment_method')
            status = form.cleaned_data.get('status')
            payee = form.cleaned_data.get('payee')
            remark = form.cleaned_data.get('remark')

            try:
                paymentrecord.date = date
                paymentrecord.student = student
                paymentrecord.course = course
                paymentrecord.learning = learning
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

                paymentrecord.save()

                # Check if lesson hours are retrieved properly
                # if paymentrecord.learning_record:
                #     # lesson_hours = paymentrecord.calculate_lesson_hours()
                #     if lesson_hours is not None:
                #         messages.success(request, _("Lesson hours retrieved successfully"))
                #     else:
                #         messages.error(request, _("Lesson hours are called but not being shown"))
                # else:
                #     messages.error(request, _("Lesson hours are not being retrieved"))

                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_payment_record', args=[payment_id]))
            except Exception as e:
                messages.error(request, "Could Not Update: " + str(e))
        else:
            messages.error(request, "Fill Form Properly")
    return render(request, 'hod_template/edit_payment_record_template.html', context)

def fetch_class_schedule(request):
    course_id = request.GET.get('course_id')
    teacher_id = request.GET.get('teacher_id')
    
    class_schedule = ClassSchedule.objects.filter(course_id=course_id, teacher_id=teacher_id).first()
    
    if class_schedule:
        data = {
            'start_time': class_schedule.start_time.strftime('%H:%M') if class_schedule.start_time else None,
            'end_time': class_schedule.end_time.strftime('%H:%M') if class_schedule.end_time else None,
            'lesson_hours': class_schedule.lesson_hours if class_schedule.lesson_hours is not None else None
        }
    else:
        data = {}
    
    return JsonResponse(data)

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
                # Compare with ClassSchedule
                class_schedule = ClassSchedule.objects.filter(course=course, teacher=teacher).first()
                if class_schedule:
                    start_time = class_schedule.start_time
                    end_time = class_schedule.end_time
                    lesson_hours = class_schedule.lesson_hours
                
                learningrecord.date = date
                learningrecord.student = student
                learningrecord.course = course
                learningrecord.teacher = teacher
                learningrecord.start_time = start_time
                learningrecord.end_time = end_time
                learningrecord.lesson_hours = lesson_hours
                
                # Get the remark from the associated student
                remark = student.admin.remark if student and student.admin else None
                learningrecord.remark = remark
                
                learningrecord.save()
              
                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_learning_record', args=[learn_id]))
            except Exception as e:
                messages.error(request, "Could Not Update: " + str(e))
        else:
            messages.error(request, "Fill Form Properly")
            
    return render(request, 'hod_template/edit_learning_record_template.html', context)

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
            start_time = form.cleaned_data.get('start_time')  # Corrected here
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
def student_feedback_message(request):
    if request.method != 'POST':
        feedbacks = FeedbackStudent.objects.all()
        context = {
            'feedbacks': feedbacks,
            'page_title': _('Student Feedback Messages')
        }
        return render(request, 'hod_template/student_feedback_template.html', context)
    else:
        feedback_id = request.POST.get('id')
        try:
            feedback = get_object_or_404(FeedbackStudent, id=feedback_id)
            reply = request.POST.get('reply')
            feedback.reply = reply
            feedback.save()
            return HttpResponse(True)
        except Exception as e:
            return HttpResponse(False)

@csrf_exempt
def teacher_feedback_message(request):
    if request.method != 'POST':
        feedbacks = FeedbackTeacher.objects.all()
        context = {
            'feedbacks': feedbacks,
            'page_title': _('teacher Feedback Messages')
        }
        return render(request, 'hod_template/teacher_feedback_template.html', context)
    else:
        feedback_id = request.POST.get('id')
        try:
            feedback = get_object_or_404(FeedbackTeacher, id=feedback_id)
            reply = request.POST.get('reply')
            feedback.reply = reply
            feedback.save()
            return HttpResponse(True)
        except Exception as e:
            return HttpResponse(False)

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
def view_student_leave(request):
    if request.method != 'POST':
        allLeave = LeaveReportStudent.objects.all()
        context = {
            'allLeave': allLeave,
            'page_title': _('Leave Applications From Students')
        }
        return render(request, "hod_template/student_leave_view.html", context)
    else:
        id = request.POST.get('id')
        status = request.POST.get('status')
        if (status == '1'):
            status = 1
        else:
            status = -1
        try:
            leave = get_object_or_404(LeaveReportStudent, id=id)
            leave.status = status
            leave.save()
            return HttpResponse(True)
        except Exception as e:
            return False

def admin_view_attendance(request):
    classess = Classes.objects.all()
    sessions = Session.objects.all()
    context = {
        'classess': classess,
        'sessions': sessions,
        'page_title': _('View Attendance')
    }

    return render(request, "hod_template/admin_view_attendance.html", context)

@csrf_exempt
def get_admin_attendance(request):
    classes_id = request.POST.get('classes')
    session_id = request.POST.get('session')
    attendance_date_id = request.POST.get('attendance_date_id')
    try:
        classes = get_object_or_404(Classes, id=classes_id)
        session = get_object_or_404(Session, id=session_id)
        attendance = get_object_or_404(
            Attendance, id=attendance_date_id, session=session)
        attendance_reports = AttendanceReport.objects.filter(
            attendance=attendance)
        json_data = []
        for report in attendance_reports:
            data = {
                _("status"):  str(report.status),
                _("name"): str(report.student)
            }
            json_data.append(data)
        return JsonResponse(json.dumps(json_data), safe=False)
    except Exception as e:
        return None

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

def admin_notify_teacher(request):
    teacher = CustomUser.objects.filter(user_type=2)
    context = {
        'page_title': _("Send Notifications To Teachers"),
        'teachers': teacher
    }
    return render(request, "hod_template/teacher_notification.html", context)

def admin_notify_student(request):
    student = CustomUser.objects.filter(user_type=3)
    context = {
        'page_title': _("Send Notifications To Students"),
        'students': student
    }
    return render(request, "hod_template/student_notification.html", context)

@csrf_exempt
def send_student_notification(request):
    id = request.POST.get('id')
    message = request.POST.get('message')
    student = get_object_or_404(Student, admin_id=id)
    try:
        url = "https://fcm.googleapis.com/fcm/send"
        body = {
            'notification': {
                'title': "Student Management System",
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

@csrf_exempt
def send_teacher_notification(request):
    id = request.POST.get('id')
    message = request.POST.get('message')
    teacher = get_object_or_404(Teacher, admin_id=id)
    try:
        url = "https://fcm.googleapis.com/fcm/send"
        body = {
            'notification': {
                'title': "Student Management System",
                'body': message,
                'click_action': reverse('teacher_view_notification'),
                'icon': static('dist/img/AdminLTELogo.png')
            },
            'to': teacher.admin.fcm_token
        }
        headers = {'Authorization':
                   'key=AAAA3Bm8j_M:APA91bElZlOLetwV696SoEtgzpJr2qbxBfxVBfDWFiopBWzfCfzQp2nRyC7_A2mlukZEHV4g1AmyC6P_HonvSkY2YyliKt5tT3fe_1lrKod2Daigzhb2xnYQMxUWjCAIQcUexAMPZePB',
                   'Content-Type': 'application/json'}
        data = requests.post(url, data=json.dumps(body), headers=headers)
        notification = NotificationTeacher(teacher=teacher, message=message)
        notification.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")

def delete_teacher(request, teacher_id):
    teacher = get_object_or_404(CustomUser, teacher__id=teacher_id)
    teacher.delete()
    messages.success(request, "teacher deleted successfully!")
    return redirect(reverse('manage_teacher'))

def delete_student(request, student_id):
    student = get_object_or_404(CustomUser, student__id=student_id)
    student.delete()
    messages.success(request, "Student deleted successfully!")
    return redirect(reverse('manage_student'))

def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    try:
        course.delete()
        messages.success(request, "Course deleted successfully!")
    except Exception:
        messages.error(
            request, "Sorry, some students are assigned to this course already. Kindly change the affected student course and try again")
    return redirect(reverse('manage_course'))

def delete_classes(request, classes_id):
    classes = get_object_or_404(Classes, id=classes_id)
    classes.delete()
    messages.success(request, "Classes deleted successfully!")
    return redirect(reverse('manage_classes'))

def delete_campus(request, campus_id):
    campus = get_object_or_404(Campus, id=campus_id)
    campus.delete()
    messages.success(request, "Campus deleted successfully!")
    return redirect(reverse('manage_campus'))

def delete_payment_record(request, payment_id):
    payment = get_object_or_404(PaymentRecord, id=payment_id)
    payment.delete()
    messages.success(request, "Record deleted Successfully!")
    return redirect(reverse('manage_payment_record'))

def delete_learning_record(request, learn_id):
    learn = get_object_or_404(LearningRecord, id=learn_id)
    learn.delete()
    messages.success(request, "Classes deleted successfully!")
    return redirect(reverse('manage_learning_record'))

def delete_class_schedule(request, schedule_id):
    schedule = get_object_or_404(ClassSchedule, id=schedule_id)
    schedule.delete()
    messages.success(request, "Class Schedule deleted successfully!")
    return redirect(reverse('manage_class_schedule'))

def delete_session(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    try:
        session.delete()
        messages.success(request, "Session deleted successfully!")
    except Exception:
        messages.error(
            request, "There are students assigned to this session. Please move them to another session.")
    return redirect(reverse('manage_session'))

