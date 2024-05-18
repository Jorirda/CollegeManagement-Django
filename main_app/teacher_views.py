import json

from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponseRedirect, get_object_or_404,redirect, render)
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist

from .forms import *
from .models import *


def teacher_home(request):
    teacher = get_object_or_404(Teacher, admin=request.user)
    total_students = LearningRecord.objects.filter(teacher_id=teacher).count() #SLIGHT TWEAKS
    total_leave = LeaveReportTeacher.objects.filter(teacher=teacher).count() 
    total_courses = ClassSchedule.objects.filter(teacher=teacher).values('course').distinct().count() #FIXED IT, COUNTS ATTENDEES
    
    # Initialize attendance variables
    total_attendance = 0
    attendance_per_course = []

    # Collecting attendance data per course
    class_schedules = ClassSchedule.objects.filter(teacher=teacher)
    courses = set(schedule.course for schedule in class_schedules)

    for course in courses:
        course_schedules = class_schedules.filter(course=course)
        course_attendance_count = Attendance.objects.filter(classes__in=course_schedules).count()
        total_attendance += course_attendance_count
        attendance_per_course.append({
            'course_name': course.name,
            'attendance_count': course_attendance_count
        })

    context = {
        'page_title': f'Teacher Panel - {teacher.admin.full_name} ({", ".join(course.name for course in courses)})',
        'total_students': total_students,
        'total_attendance': total_attendance,
        'total_leave': total_leave,
        'total_courses': total_courses,
        'attendance_per_course': attendance_per_course
    }
    return render(request, 'teacher_template/home_content.html', context)

def teacher_view_profile(request):
    teacher = get_object_or_404(Teacher, admin=request.user)
    form = TeacherEditForm(request.POST or None, request.FILES or None, instance=teacher)
    context = {'form': form, 'page_title': 'View/Update Profile'}

    if request.method == 'POST':
        try:
            if form.is_valid():
                full_name = form.cleaned_data.get('full_name')
                password = form.cleaned_data.get('password')
                gender = form.cleaned_data.get('gender')
                passport = request.FILES.get('profile_pic')

                admin = teacher.admin

                if password:
                    admin.set_password(password)
                if passport:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    admin.profile_pic = passport_url
                
                admin.full_name = full_name
                admin.gender = gender
                admin.save()
                teacher.save()

                messages.success(request, "Profile Updated!")
                return redirect(reverse('teacher_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
        except Exception as e:
            messages.error(request, f"Error Occurred While Updating Profile: {e}")
    
    return render(request, "teacher_template/teacher_view_profile.html", context)

def teacher_take_attendance(request):
    teacher = get_object_or_404(Teacher, admin=request.user)
    print(teacher)
    classes = ClassSchedule.objects.filter(teacher=teacher)
    sessions = Session.objects.all()
    context = {
        'classes': classes,
        'sessions': sessions,
        'page_title': 'Take Attendance'
    }

    return render(request, 'teacher_template/teacher_take_attendance.html', context)

def teacher_update_attendance(request):
    teacher = get_object_or_404(Teacher, admin=request.user)
    classess = Course.objects.filter(teacher_id=teacher)
    sessions = Session.objects.all()
    context = {
        'classess': classess,
        'sessions': sessions,
        'page_title': 'Update Attendance'
    }

    return render(request, 'teacher_template/teacher_update_attendance.html', context)

def teacher_apply_leave(request):
    form = LeaveReportTeacherForm(request.POST or None)
    teacher = get_object_or_404(Teacher, admin_id=request.user.id)
    context = {
        'form': form,
        'leave_history': LeaveReportTeacher.objects.filter(teacher=teacher),
        'page_title': 'Apply for Leave'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.teacher = teacher
                obj.save()
                messages.success(
                    request, "Application for leave has been submitted for review")
                return redirect(reverse('teacher_apply_leave'))
            except Exception:
                messages.error(request, "Could not apply!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "teacher_template/teacher_apply_leave.html", context)

def teacher_feedback(request):
    form = FeedbackTeacherForm(request.POST or None)
    teacher = get_object_or_404(Teacher, admin_id=request.user.id)
    context = {
        'form': form,
        'feedbacks': FeedbackTeacher.objects.filter(teacher=teacher),
        'page_title': 'Add Feedback'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.teacher = teacher
                obj.save()
                messages.success(request, "Feedback submitted for review")
                return redirect(reverse('teacher_feedback'))
            except Exception:
                messages.error(request, "Could not Submit!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "teacher_template/teacher_feedback.html", context)

def teacher_view_notification(request):
    teacher = get_object_or_404(Teacher, admin=request.user)
    notifications = NotificationTeacher.objects.filter(teacher=teacher)
    context = {
        'notifications': notifications,
        'page_title': "View Notifications"
    }
    return render(request, "teacher_template/teacher_view_notification.html", context)

def teacher_add_result(request):
    form = ResultForm(request.POST or None)
    context = {'form': form, 'page_title': 'Add Result'}
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Result Added")
                return redirect(reverse('teacher_add_result'))
            except Exception as e:
                messages.error(request, 'Could Not Add ' + str(e))
        else:
            messages.error(request, 'Fill Form Properly ')
    return render(request, "teacher_template/teacher_view_profile.html", context)


#Exempts
@csrf_exempt
def get_students(request):
    classes_id = request.POST.get('classes')
    session_id = request.POST.get('session')
    try:
        classes = get_object_or_404(ClassSchedule, id=classes_id)
        print("hi")
        print(classes)
        session = get_object_or_404(Session, id=session_id)
        students = Student.objects.filter(
            course_id=classes.course)
        student_data = []
        for student in students:
            data = {
                    "id": student.id,
                    "name":  student.admin.full_name
                    }
            student_data.append(data)
        return JsonResponse(json.dumps(student_data), content_type='application/json', safe=False)
    except Exception as e:
        return e
    
@csrf_exempt
def save_attendance(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=405)

    student_data = request.POST.get('student_ids')
    date = request.POST.get('date')
    classes_id = request.POST.get('classes')
    session_id = request.POST.get('session')

    if not (student_data and date and classes_id and session_id):
        return JsonResponse({'error': 'Missing data'}, status=400)

    try:
        students = json.loads(student_data)
        session = get_object_or_404(Session, id=session_id)
        classes = get_object_or_404(ClassSchedule, id=classes_id)
        attendance = Attendance(session=session, classes=classes, date=date)
        attendance.save()

        for student_dict in students:
            student = get_object_or_404(Student, id=student_dict.get('id'))
            status = student_dict.get('status', 0)  # Assuming '0' as default status if not provided
            attendance_report = AttendanceReport(student=student, attendance=attendance, status=status)
            attendance_report.save()
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except ObjectDoesNotExist as e:
        return JsonResponse({'error': str(e)}, status=404)
    except Exception as e:
        # Log the exception for debugging purposes
        # Consider using logging here instead of printing
        print("An error occurred:", e)
        return JsonResponse({'error': 'Server error'}, status=500)

    return HttpResponse("OK")

@csrf_exempt
def get_student_attendance(request):
    attendance_date_id = request.POST.get('attendance_date_id')
    try:
        date = get_object_or_404(Attendance, id=attendance_date_id)
        attendance_data = AttendanceReport.objects.filter(attendance=date)
        student_data = []
        for attendance in attendance_data:
            data = {"id": attendance.student.admin.id,
                    "name": attendance.student.admin.last_name + " " + attendance.student.admin.first_name,
                    "status": attendance.status}
            student_data.append(data)
        return JsonResponse(json.dumps(student_data), content_type='application/json', safe=False)
    except Exception as e:
        return e

@csrf_exempt
def update_attendance(request):
    student_data = request.POST.get('student_ids')
    date = request.POST.get('date')
    students = json.loads(student_data)
    try:
        attendance = get_object_or_404(Attendance, id=date)

        for student_dict in students:
            student = get_object_or_404(
                Student, admin_id=student_dict.get('id'))
            attendance_report = get_object_or_404(AttendanceReport, student=student, attendance=attendance)
            attendance_report.status = student_dict.get('status')
            attendance_report.save()
    except Exception as e:
        return None

    return HttpResponse("OK")

@csrf_exempt
def teacher_fcmtoken(request):
    token = request.POST.get('token')
    try:
        teacher_user = get_object_or_404(CustomUser, id=request.user.id)
        teacher_user.fcm_token = token
        teacher_user.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")

@csrf_exempt
def fetch_student_result(request):
    try:
        classes_id = request.POST.get('classes')
        student_id = request.POST.get('student')
        student = get_object_or_404(Student, id=student_id)
        classes = get_object_or_404(Classes, id=classes_id)
        result = StudentResult.objects.get(student=student, classes=classes)
        result_data = {
            'exam': result.exam,
            'test': result.test
        }
        return HttpResponse(json.dumps(result_data))
    except Exception as e:
        return HttpResponse('False')
