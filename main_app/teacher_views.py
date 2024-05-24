import json
import logging

from django.core.paginator import Paginator
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import (HttpResponseRedirect, get_object_or_404,redirect, render)
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _


from .forms import *
from .models import *

# Get an instance of a logger
logger = logging.getLogger(__name__)

#Get and fetch functions
def get_attendance_students(request):
    if request.method == 'POST' and request.is_ajax():
        class_id = request.POST.get('class_id')
        session_id = request.POST.get('session_id')
        date = request.POST.get('date')

        students = Student.objects.filter(classes__id=class_id, classes__session__id=session_id).distinct()
        attendance = Attendance.objects.filter(classes__id=class_id, session__id=session_id, date=date).first()
        attendance_reports = AttendanceReport.objects.filter(attendance=attendance) if attendance else []

        student_data = []
        for student in students:
            status = False
            for report in attendance_reports:
                if report.student.id == student.id:
                    status = report.status
                    break
            student_data.append({'id': student.id, 'name': student.admin.full_name, 'status': status})

        return JsonResponse(student_data, safe=False)

@csrf_exempt
def get_students(request):
    classes_id = request.POST.get('classes')
    session_id = request.POST.get('session')

    try:
        classes = get_object_or_404(ClassSchedule, id=classes_id)
        session = get_object_or_404(Session, id=session_id)

        # Fetch students related to the selected class/course
        learning_records = LearningRecord.objects.filter(course=classes.course)
        student_data = [
            {"id": record.student.id, "name": record.student.admin.full_name,}
            for record in learning_records
        ]

        return JsonResponse(student_data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def get_student_attendance(request):
    attendance_date_id = request.POST.get('attendance_date_id')
    try:
        date = get_object_or_404(Attendance, id=attendance_date_id)
        attendance_data = AttendanceReport.objects.filter(attendance=date)
        student_data = []
        for attendance in attendance_data:
            data = {"id": attendance.student.admin.id,
                    "name": attendance.student.admin.full_name,
                    "status": attendance.status}
            student_data.append(data)
        return JsonResponse(json.dumps(student_data), content_type='application/json', safe=False)
    except Exception as e:
        return e
    
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

#teacher
def teacher_home(request):
    teacher = get_object_or_404(Teacher, admin=request.user)
    total_students = LearningRecord.objects.filter(teacher_id=teacher).count()
    total_leave = LeaveReportTeacher.objects.filter(teacher=teacher).count()
    total_courses = ClassSchedule.objects.filter(teacher=teacher).values('course').distinct().count()

    # Get filter values from request
    course_id = request.GET.get('course')
    class_schedule_id = request.GET.get('class_schedule')
    student_id = request.GET.get('student')

    # Filter class schedules by teacher and optional course and class_schedule
    class_schedules = ClassSchedule.objects.filter(teacher=teacher)
    if course_id:
        class_schedules = class_schedules.filter(course_id=course_id)
    if class_schedule_id:
        class_schedules = class_schedules.filter(id=class_schedule_id)

    # Filter students by learning records and optional student_id
    students = Student.objects.filter(learningrecord__schedule_record__in=class_schedules).distinct()
    if student_id:
        students = students.filter(id=student_id)

    # Collect attendance data per class schedule
    total_attendance = Attendance.objects.filter(classes__in=class_schedules).count()
    attendance_per_schedule = [
        {
            'schedule_name': schedule.course.name,
            'attendance_count': AttendanceReport.objects.filter(attendance__classes=schedule).count()
        }
        for schedule in class_schedules
    ]

    if request.is_ajax():
        # Return students if requested
        if 'get_students' in request.GET:
            student_data = [
                {'id': student.id, 'full_name': student.admin.full_name}
                for student in students
            ]
            return JsonResponse({'students': student_data})

        # Return attendance data
        if student_id:
            attendance_data = [
                {
                    'schedule_name': schedule.course.name,
                    'attendance_count': AttendanceReport.objects.filter(attendance__classes=schedule, student_id=student_id).count()
                }
                for schedule in class_schedules
            ]
        else:
            attendance_data = attendance_per_schedule

        data = {
            'labels': [item['schedule_name'] for item in attendance_data],
            'attendance_counts': [item['attendance_count'] for item in attendance_data]
        }
        return JsonResponse({'data': data})

    context = {
        'page_title': f'教师 - {teacher.admin.full_name}',
        'total_students': total_students,
        'total_attendance': total_attendance,
        'total_leave': total_leave,
        'total_courses': total_courses,
        'attendance_per_schedule': attendance_per_schedule,
        'students': students,
        'courses': Course.objects.all(),
        'class_schedules': ClassSchedule.objects.filter(teacher=teacher),
    }
    return render(request, 'teacher_template/home_content.html', context)

def get_class_schedules(request):
    course_id = request.GET.get('course_id')
    class_schedules = ClassSchedule.objects.filter(course_id=course_id)
    response = [
        {
            'id': schedule.id,
            'start_time': schedule.start_time.strftime('%H:%M'),
            'end_time': schedule.end_time.strftime('%H:%M')
        }
        for schedule in class_schedules
    ]
    return JsonResponse(response, safe=False)

@csrf_exempt
def get_students(request):
    if request.method == 'POST':
        course_id = request.POST.get('course')
        class_schedule_id = request.POST.get('class_schedule')
        students = Student.objects.filter(learningrecord__schedule_record__id=class_schedule_id).distinct()
        response = [
            {
                'id': student.id,
                'full_name': student.admin.full_name
            }
            for student in students
        ]
        return JsonResponse({'students': response})
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=405)

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


#attendance
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

def teacher_edit_attendance(request, attendance_id):
    instance = get_object_or_404(Attendance, id=attendance_id)

    # Initial data for the form
    initial_data = {
        'classes': instance.classes,
    }

    form = TeacherEditAttendanceForm(request.POST or None, instance=instance, initial=initial_data)

    # Get related students and attendance reports
    attendance_reports = AttendanceReport.objects.filter(attendance=instance)
    student_ids = attendance_reports.values_list('student_id', flat=True)
    students = Student.objects.filter(id__in=student_ids)

    for student in students:
        student.attendance_status = attendance_reports.get(student=student).status

    if request.method == 'POST' and request.is_ajax():
        if form.is_valid():
            form.save()
            student_data = request.POST.getlist('student_data[]')

            # Update attendance status for each student
            for student in students:
                attendance_report = attendance_reports.get(student=student)
                attendance_report.status = str(student.id) in student_data
                attendance_report.save()

            return JsonResponse({'success': True, 'message': 'Attendance saved successfully'})
        else:
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'message': 'Failed to update attendance', 'errors': errors}, status=400)

    context = {
        'form': form,
        'students': students,
        'attendance_id': attendance_id,
        'page_title': _('Edit Attendance')
    }

    return render(request, "teacher_template/teacher_edit_attendance.html", context)

def teacher_view_attendance(request):
    attendance_id = request.GET.get('attendance_id')
    attendance = get_object_or_404(Attendance, id=attendance_id)
    student_attendances = AttendanceReport.objects.filter(attendance=attendance)

    attendance_details = [
        {
            'student_name': student_attendance.student.admin.full_name,
            'is_present': student_attendance.status
        }
        for student_attendance in student_attendances
    ]

    return JsonResponse({'success': True, 'attendance_details': attendance_details})

@csrf_exempt
def save_attendance(request):
    if request.method != 'POST':
        logging.error('Invalid request method')
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

    logging.debug('Processing POST request')
    student_data = request.POST.get('student_ids')
    date = request.POST.get('date')
    classes_id = request.POST.get('classes')
    session_id = request.POST.get('session')

    logging.debug(f'Received data: student_data={student_data}, date={date}, classes_id={classes_id}, session_id={session_id}')

    if not (student_data and date and classes_id and session_id):
        logging.error('Missing data')
        return JsonResponse({'success': False, 'error': 'Missing data'}, status=400)

    try:
        students = json.loads(student_data)
        session = get_object_or_404(Session, id=session_id)
        classes = get_object_or_404(ClassSchedule, id=classes_id)
        attendance = Attendance(session=session, classes=classes, date=date)
        logging.debug(f'Created Attendance object: {attendance}')
        attendance.save()
        logging.debug('Attendance object saved')

        for student_dict in students:
            student_id = student_dict.get('id')
            if student_id is None:
                logging.error('Student ID is undefined')
                return JsonResponse({'success': False, 'error': 'Student ID is undefined'}, status=400)
            student_status = student_dict.get('status', 0)
            student = get_object_or_404(Student, id=student_id)
            attendance_report = AttendanceReport(student=student, attendance=attendance, status=student_status)
            logging.debug(f'Creating AttendanceReport object: {attendance_report}')
            attendance_report.save()
            logging.debug('AttendanceReport object saved')

        logging.debug('Attendance and AttendanceReport objects saved successfully')
        return JsonResponse({'success': True, 'message': 'Attendance saved successfully'})
    except json.JSONDecodeError:
        logging.error('Invalid JSON')
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logging.error(f'Unexpected error: {str(e)}')
        return JsonResponse({'success': False, 'error': f'An unexpected error occurred: {str(e)}'}, status=500)

def teacher_delete_attendance(request):
    if request.method == 'POST' and request.is_ajax():
        attendance_id = request.POST.get('attendance_id')
        try:
            attendance = get_object_or_404(Attendance, id=attendance_id)
            attendance.delete()
            return JsonResponse({'success': True})
        except Attendance.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Attendance does not exist'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method or not an AJAX request'})
    
def teacher_manage_attendance(request):
    teacher = get_object_or_404(Teacher, admin=request.user)
    attendances = Attendance.objects.filter(classes__teacher=teacher)
    
    paginator = Paginator(attendances, 10)  # Show 10 records per page
    page_number = request.GET.get('page')
    paginated_attendances = paginator.get_page(page_number)

    context = {
        'attendances': paginated_attendances,
        'page_title': _('Manage Attendance'),
    }
    return render(request, 'teacher_template/teacher_manage_attendance.html', context)

@login_required
def teacher_courses(request):
    # Filter learning records based on the current teacher logged in
    current_teacher = request.user.teacher
    learningrecords = LearningRecord.objects.filter(teacher=current_teacher)

    paginator = Paginator(learningrecords, 10)  # Show 10 records per page
    page_number = request.GET.get('page')
    paginated_records = paginator.get_page(page_number)
    
    context = {
        'learningrecords': paginated_records,  # Pass the paginated queryset to the template
        'page_title': _('Teacher Courses'),
    }
    return render(request, 'teacher_template/teacher_courses.html', context)

#leave
def teacher_apply_leave(request):
    form = LeaveReportTeacherForm(request.POST or None)
    teacher = get_object_or_404(Teacher, admin_id=request.user.id)
    leave_history = LeaveReportTeacher.objects.filter(teacher=teacher)
    context = {
        'form': form,
        'leave_history': leave_history,
        'page_title': 'Apply for Leave'
    }
    
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.teacher = teacher
                obj.save()
                return JsonResponse({'success': True, 'message': 'Application for leave has been submitted for review'})
            except Exception as e:
                return JsonResponse({'success': False, 'message': 'Could not apply. Error: {}'.format(str(e))})
        else:
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'errors': errors})

    return render(request, "teacher_template/teacher_apply_leave.html", context)


#Summary
@csrf_exempt
def teacher_write_summary(request):
    teacher = get_object_or_404(Teacher, admin_id=request.user.id)
    form = SummaryTeacherForm(request.POST or None, teacher=teacher)
    summaries = SummaryTeacher.objects.filter(teacher=teacher).order_by('-created_at')

    if request.method == 'POST':
        if 'edit' in request.POST and request.POST.get('edit') == 'true':
            summary_id = request.POST.get('id')
            try:
                summary = get_object_or_404(SummaryTeacher, id=summary_id)
                new_summary_text = request.POST.get('summary')
                summary.summary = new_summary_text
                summary.replied_at = timezone.now()
                summary.save()
                return HttpResponse("True")
            except Exception as e:
                return HttpResponse("False")
        if 'delete' in request.POST and request.POST.get('delete') == 'true':
            summary_id = request.POST.get('id')
            try:
                summary = get_object_or_404(SummaryTeacher, id=summary_id)
                summary.delete()
                return HttpResponse("True")
            except Exception as e:
                return HttpResponse("False")
        else:
            if form.is_valid():
                try:
                    obj = form.save(commit=False)
                    obj.teacher = teacher
                    obj.save()
                    messages.success(request, "Summary submitted for review")
                    return redirect(reverse('teacher_write_summary'))
                except Exception:
                    messages.error(request, "Could not submit!")
            else:
                messages.error(request, "Form has errors!")

    context = {
        'form': form,
        'summaries': summaries,
        'page_title': _('Add Summary')
    }

    return render(request, 'teacher_template/teacher_write_summary.html', context)




#Notifications
def teacher_view_notification(request):
    teacher = get_object_or_404(Teacher, admin=request.user)
    
    # Fetch notifications and related objects in fewer queries
    notifications = NotificationTeacher.objects.filter(teacher=teacher).select_related(
        'payment_record__learning_record', 'student__admin', 'course'
    )
    
    annotated_notifications = [
        {
            'id': notification.id,
            'date': notification.date,
            'time': notification.time,
            'message': notification.message,
            'is_read': notification.is_read,
            'course_name': notification.course.name if notification.course else 'N/A',
            'course_start': notification.payment_record.learning_record.start_time if notification.payment_record and notification.payment_record.learning_record else 'N/A',
            'course_end': notification.payment_record.learning_record.end_time if notification.payment_record and notification.payment_record.learning_record else 'N/A',
            'student_name': notification.student.admin.full_name if notification.student else 'N/A',
            'next_payment_date': notification.payment_record.next_payment_date if notification.payment_record else 'N/A'
        }
        for notification in notifications
    ]

    context = {
        'notifications': annotated_notifications,
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
        # logger.error(f"Error fetching notification count: {e}")
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

def teacher_delete_notification(request):
    if request.method == 'POST' and request.is_ajax():
        notification_id = request.POST.get('notification_id')
        try:
            notification = get_object_or_404(NotificationTeacher, id=notification_id)
            notification.delete()
            return JsonResponse({'success': True})
        except NotificationTeacher.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Notification does not exist'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method or not an AJAX request'})


#Result
# def teacher_add_result(request):
#     form = ResultForm(request.POST or None)
#     teacher = get_object_or_404(Teacher, admin=request.user)
#     classes = ClassSchedule.objects.filter(teacher=teacher)
#     sessions = Session.objects.all()
#     context = {'form': form, 'page_title': 'Add Result','classes': classes,
#         'sessions': sessions,}
#     if request.method == 'POST':
#         if form.is_valid():
#             try:
#                 form.save()
#                 messages.success(request, "Result Added")
#                 return redirect(reverse('teacher_add_result'))
#             except Exception as e:
#                 messages.error(request, 'Could Not Add ' + str(e))
#         else:
#             messages.error(request, 'Fill Form Properly ')
#     return render(request, "teacher_template/teacher_add_result.html", context)

# def teacher_edit_result(request):
#     form = ResultForm(request.POST or None)
#     teacher = get_object_or_404(Teacher, admin=request.user)
#     classes = ClassSchedule.objects.filter(teacher=teacher)
#     sessions = Session.objects.all()
#     context = {'form': form, 'page_title': 'Edit Result','classes': classes,
#         'sessions': sessions,}
#     if request.method == 'POST':
#         if form.is_valid():
#             try:
#                 form.save()
#                 messages.success(request, "Result Edited")
#                 return redirect(reverse('teacher_edit_result'))
#             except Exception as e:
#                 messages.error(request, 'Could Not Add ' + str(e))
#         else:
#             messages.error(request, 'Fill Form Properly ')
#     return render(request, "teacher_template/teacher_edit_result.html", context)


#Exempts
# @csrf_exempt
# def update_attendance(request):
#     student_data = request.POST.get('student_ids')
#     date = request.POST.get('date')
#     students = json.loads(student_data)
#     try:
#         attendance = get_object_or_404(Attendance, id=date)

#         for student_dict in students:
#             student = get_object_or_404(
#                 Student, admin_id=student_dict.get('id'))
#             attendance_report = get_object_or_404(AttendanceReport, student=student, attendance=attendance)
#             attendance_report.status = student_dict.get('status')
#             attendance_report.save()
#     except Exception as e:
#         return None

#     return HttpResponse("OK")

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

@login_required
def student_renewals(request):
    students = Student.objects.all()
    today = timezone.now().date()
    renewals = []

    for student in students:
        last_payment = PaymentRecord.objects.filter(student=student).order_by('-date').first()
        if last_payment:
            status = 'Pending' if today <= last_payment.next_payment_date else 'Outstanding'
            renewals.append({
                'student': student,
                'course': last_payment.course,
                'payment_amount': last_payment.amount_due,
                'next_payment_date': last_payment.next_payment_date,
                'status': status,
            })

    context = {
        'renewals': renewals,
        'page_title': 'Student Renewals'
    }
    return render(request, 'teacher_template/student_renewals.html', context)

@login_required
def renew_student(request, student_id):
    if request.method == 'POST' and request.is_ajax():
        student = get_object_or_404(Student, id=student_id)
        last_payment = PaymentRecord.objects.filter(student=student).order_by('-date').first()
        
        if last_payment:
            new_payment_date = last_payment.next_payment_date + timedelta(days=30)  # Assuming monthly renewal
            PaymentRecord.objects.create(
                date=timezone.now().date(),
                next_payment_date=new_payment_date,
                student=student,
                course=last_payment.course,
                lesson_unit_price=last_payment.lesson_unit_price,
                discounted_price=last_payment.discounted_price,
                book_costs=last_payment.book_costs,
                other_fee=last_payment.other_fee,
                amount_due=last_payment.amount_paid,  # Use the amount paid from the last payment as the new amount due
                amount_paid=0,  # Initially unpaid
                payment_method=last_payment.payment_method,
                status='Pending',
                payee=last_payment.payee,
                remark='Renewal payment',
                lesson_hours=last_payment.lesson_hours,
                learning_record=last_payment.learning_record  # Use the same learning record
            )
            student.admin.total_semester += 1
            student.save()

            return JsonResponse({'success': True, 'message': "Student renewed successfully!"})
        else:
            return JsonResponse({'success': False, 'message': "No previous payment record found for the student."})
    return JsonResponse({'success': False, 'message': "Invalid request method."})


@login_required
def withdraw_student(request, student_id):
    if request.method == 'POST' and request.is_ajax():
        student = get_object_or_404(Student, id=student_id)
        student.status = 'Withdrawn'  # or 'Withdrawn'
        student.save()

        return JsonResponse({'success': True, 'message': "Student status updated to Withdrawn."})
    return JsonResponse({'success': False, 'message': "Invalid request method."})