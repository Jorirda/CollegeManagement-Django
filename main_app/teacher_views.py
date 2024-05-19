import json
import logging

from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponseRedirect, get_object_or_404,redirect, render)
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from .forms import *
from .models import *

# Get an instance of a logger
logger = logging.getLogger(__name__)

def teacher_home(request):
    teacher = get_object_or_404(Teacher, admin=request.user)
    total_students = Student.objects.filter(course=teacher.course).count()
    total_leave = LeaveReportTeacher.objects.filter(teacher=teacher).count()
    classess = Classes.objects.filter(teacher=teacher)
    total_classes = classess.count()

    # Retrieve ClassSchedule objects related to the classes taught by the teacher
    class_schedule_list = ClassSchedule.objects.filter(course__in=classess.values('course'))
    attendance_list = Attendance.objects.filter(classes__in=class_schedule_list)
    total_attendance = attendance_list.count()

    # Collecting attendance data per class
    attendance_list = []
    classes_list = []
    for classes in classess:
        # Get ClassSchedule objects for each class
        class_schedules = ClassSchedule.objects.filter(course=classes.course, teacher=classes.teacher)
        attendance_count = Attendance.objects.filter(classes__in=class_schedules).count()
        classes_list.append(classes.name)
        attendance_list.append(attendance_count)

    context = {
        'page_title': 'Teacher Panel - ' + str(teacher.admin.last_name) + ' (' + str(teacher.course) + ')',
        'total_students': total_students,
        'total_attendance': total_attendance,
        'total_leave': total_leave,
        'total_classes': total_classes,
        'classes_list': classes_list,
        'attendance_list': attendance_list
    }
    return render(request, 'teacher_template/home_content.html', context)

def teacher_view_profile(request):
    teacher = get_object_or_404(Teacher, admin=request.user)
    form = TeacherEditForm(request.POST or None, request.FILES or None,instance=teacher)
    context = {'form': form, 'page_title': 'View/Update Profile'}
    if request.method == 'POST':
        try:
            if form.is_valid():
                # first_name = form.cleaned_data.get('first_name')
                # last_name = form.cleaned_data.get('last_name')
                full_name = form.cleaned_data.get('full_name')
                password = form.cleaned_data.get('password') or None
                gender = form.cleaned_data.get('gender')
                passport = request.FILES.get('profile_pic') or None
                admin = teacher.admin
                if password != None:
                    admin.set_password(password)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    admin.profile_pic = passport_url
                # admin.first_name = first_name
                # admin.last_name = last_name
                admin.full_name = full_name
                # admin.address = address
                admin.gender = gender
                admin.save()
                teacher.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('teacher_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
                return render(request, "teacher_template/teacher_view_profile.html", context)
        except Exception as e:
            messages.error(
                request, "Error Occured While Updating Profile " + str(e))
            return render(request, "teacher_template/teacher_view_profile.html", context)

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

#Notifications
def teacher_view_notification(request):
    teacher = get_object_or_404(Teacher, admin=request.user)
    notifications = NotificationTeacher.objects.filter(teacher=teacher)
    context = {
        'notifications': notifications,
        'page_title': "View Notifications"
    }
    return render(request, "teacher_template/teacher_view_notification.html", context)

@login_required
def teacher_view_notification_count(request):
    try:
        teacher = request.user.teacher
        unread_notifications_count = NotificationTeacher.objects.filter(teacher=teacher, is_read=False).count()
        return JsonResponse({'count': unread_notifications_count})
    except Exception as e:
        logger.error(f"Error fetching notification count: {e}")
        return JsonResponse({'count': 0})

# View to fetch the count of unread notifications for the teacher
@login_required
def mark_notification_as_read(request, notification_id):
    try:
        notification = get_object_or_404(NotificationTeacher, id=notification_id, teacher=request.user.teacher)
        notification.is_read = True
        notification.save()
        return redirect('teacher_view_notification')
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        return redirect('teacher_view_notification')

def teacher_delete_notification(request, notification_id):
    try:
        notification = get_object_or_404(NotificationTeacher, id=notification_id)
        notification.delete()
        messages.success(request, "Notification Deleted Successfully!")
    except Exception as e:
        logger.error(f"An error occurred while deleting the notification with ID {notification_id}: {e}")
        messages.error(request, "An error occurred while deleting the notification.")
    return redirect(reverse('teacher_view_notification'))

def teacher_add_result(request):
    teacher = get_object_or_404(Teacher, admin=request.user)
    classess = Classes.objects.filter(teacher=teacher)
    sessions = Session.objects.all()
    context = {
        'page_title': 'Result Upload',
        'classess': classess,
        'sessions': sessions
    }
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

# @csrf_exempt
# def fetch_student_result(request):
#     try:
#         classes_id = request.POST.get('classes')
#         student_id = request.POST.get('student')
#         student = get_object_or_404(Student, id=student_id)
#         classes = get_object_or_404(Classes, id=classes_id)
#         result = StudentResult.objects.get(student=student, classes=classes)
#         result_data = {
#             'exam': result.exam,
#             'test': result.test
#         }
#         return HttpResponse(json.dumps(result_data))
#     except Exception as e:
#         return HttpResponse('False')