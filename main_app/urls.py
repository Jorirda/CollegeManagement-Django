"""college_management_system URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from django.conf import settings
from main_app.EditResultView import EditResultView
from django.conf.urls.static import static
from . import hod_views, teacher_views, student_views, views
import generate

urlpatterns = [
#hodviews
   
    path('ajax/get-amount-due/', hod_views.get_amount_due, name='get_amount_due'), 
    path('ajax/get-lesson-hours/', hod_views.get_lesson_hours, name='get_lesson_hours'),
    path('process_data/', generate.process_data, name='process_data'),
    path('ajax/get-teachers/', hod_views.get_teachers, name='get_teachers'),
    path('ajax/get-schedule/', hod_views.get_schedule, name='get_schedule'),
    path('renewals/', teacher_views.student_renewals, name='student_renewals'),
    path('renew_student/<int:student_id>/', teacher_views.renew_student, name='renew_student'),
    path('withdraw_student/<int:student_id>/', teacher_views.withdraw_student, name='withdraw_student'),
    path('teacher_home/', teacher_views.teacher_home, name='teacher_home'),
    path('get_class_schedules/', teacher_views.get_class_schedules, name='get_class_schedules'),
    path('get_students/', teacher_views.get_students, name='get_students'),
    path('admin_get_teacher_class_schedules_count/', hod_views.admin_get_teacher_class_schedules_count, name='admin_get_teacher_class_schedules_count'),
    path('admin_get_student_attendance/', hod_views.admin_get_student_attendance, name='admin_get_student_attendance'),
    path('get-grade-choices/', hod_views.get_grade_choices, name='get-grade-choices'),
    path("", views.login_page, name='login_page'),
    path("get_attendance", views.get_attendance, name='get_attendance'),
    path("firebase-messaging-sw.js", views.showFirebaseJS, name='showFirebaseJS'),
    path("doLogin/", views.doLogin, name='user_login'),
    path("logout_user/", views.logout_user, name='user_logout'),
    path("admin/home/", hod_views.admin_home, name='admin_home'),
    # path("teacher/query", hod_views.view_teacher_query, name='view_teacher_query'),
    path("student/query", hod_views.manage_student_query, name='manage_student_query'),
    # path("send_student_notification/", hod_views.send_student_notification,name='send_student_notification'),
    path("send_teacher_notification/", hod_views.send_teacher_notification,name='send_teacher_notification'),
    path("send_tuition_reminder/", hod_views.send_tuition_reminder,name='send_tuition_reminder'),

    path("add_session/", hod_views.add_session, name='add_session'),
    path("teacher/add", hod_views.add_teacher, name='add_teacher'),
    path("course/add", hod_views.add_course, name='add_course'),
    path("student/add/", hod_views.add_student, name='add_student'),
    path("classes/add/", hod_views.add_classes, name='add_classes'),
    # path("institution/add/", hod_views.add_institution, name='add_institution'),
    path("campus/add/", hod_views.add_campus, name='add_campus'),
    path("payment/add", hod_views.add_payment_record, name='add_payment_record'),
    path("learn/add", hod_views.add_learning_record, name='add_learning_record'),
    path("schedule/add", hod_views.add_class_schedule, name='add_class_schedule'),

    path("admin_notify_student", hod_views.admin_notify_student,name='admin_notify_student'),
    path("admin_notify_teacher", hod_views.admin_notify_teacher,name='admin_notify_teacher'),
    path("admin_send_tuition_reminder", hod_views.admin_send_tuition_reminder, name='admin_send_tuition_reminder'),
    path("admin_view_profile", hod_views.admin_view_profile,name='admin_view_profile'),
    path("check_email_availability", hod_views.check_email_availability,name="check_email_availability"),
    path("session/manage/", hod_views.manage_session, name='manage_session'),
    path("session/edit/<int:session_id>",hod_views.edit_session, name='edit_session'),
    # path("student/view/summary/", hod_views.student_summary_message,name="student_summary_message",),
    path("teacher/view/summary/", hod_views.view_teacher_summary, name="view_teacher_summary",),
    path("teacher/delete/summary/", hod_views.delete_teacher_summary, name="delete_teacher_summary"),
    # path("student/view/leave/", hod_views.view_student_leave,name="view_student_leave",),
    path("teacher/view/leave/", hod_views.view_teacher_leave, name="view_teacher_leave",),
    path("attendance/view/", hod_views.admin_view_attendance,name="admin_view_attendance",),
    path("attendance/fetch/", hod_views.get_admin_attendance,name='get_admin_attendance'),
    path('get_attendance_dates/', hod_views.get_attendance_dates, name='get_attendance_dates'),
    path("upload/", hod_views.get_upload,name='get_upload'),
    path("result", hod_views.get_result,name='get_result'),
    path('check_columns/', hod_views.check_columns, name='check_columns'),
    path('refunds', hod_views.refund_records, name='refund_records'),


    #manage
    path("teacher/manage/", hod_views.manage_teacher, name='manage_teacher'),
    path("student/manage/", hod_views.manage_student, name='manage_student'),
    path("course/manage/", hod_views.manage_course, name='manage_course'),
    path("classes/manage", hod_views.manage_classes, name='manage_classes'),
    path("campus/manage/", hod_views.manage_campus, name='manage_campus'),
    path("payment/manage/", hod_views.manage_payment_record, name='manage_payment_record'),
    path("learn/manage/", hod_views.manage_learning_record, name='manage_learning_record'),
    path("schedule/manage/", hod_views.manage_class_schedule, name='manage_class_schedule'),
    path("student/query", hod_views.manage_student_query, name = "manage_student_query"),
    path("teacher/query", hod_views.manage_teacher_query, name = "manage_teacher_query"),

    #edit
    path("teacher/edit/<int:teacher_id>", hod_views.edit_teacher, name='edit_teacher'),
    path("student/edit/<int:student_id>", hod_views.edit_student, name='edit_student'),
    path("course/edit/<int:course_id>",hod_views.edit_course, name='edit_course'),
    path('classes/edit<int:classes_id>/', hod_views.edit_classes, name='edit_classes'),
    path("campus/edit/<int:campus_id>",hod_views.edit_campus, name='edit_campus'),
    path("payment/edit/<int:payment_id>",hod_views.edit_payment_record, name='edit_payment_record'),
    path("learn/edit/<int:learn_id>",hod_views.edit_learning_record, name='edit_learning_record'),
    path("schedule/edit/<int:schedule_id>",hod_views.edit_class_schedule, name='edit_class_schedule'),
    # path('fetch-class-schedule/', hod_views.fetch_class_schedule, name='fetch_class_schedule'),
    # path('filter-teachers/', hod_views.filter_teachers, name='filter_teachers'),

    #delete
    path("teacher/delete/<int:teacher_id>",hod_views.delete_teacher, name='delete_teacher'),
    path("course/delete/<int:course_id>",hod_views.delete_course, name='delete_course'),
    path("classes/delete/<int:classes_id>",hod_views.delete_classes, name='delete_classes'),
    path("session/delete/<int:session_id>",hod_views.delete_session, name='delete_session'),
    path("student/delete/<int:student_id>",hod_views.delete_student, name='delete_student'),
    path('delete_campus/<int:campus_id>/', hod_views.delete_campus, name='delete_campus'),
    path("payment/delete/<int:payment_id>",hod_views.delete_payment_record, name='delete_payment_record'),
    path("learn/delete/<int:learn_id>",hod_views.delete_learning_record, name='delete_learning_record'),
    path("schedule/delete/<int:schedule_id>",hod_views.delete_class_schedule, name='delete_class_schedule'),
   
    # teacher
    path("teacher/home/", teacher_views.teacher_home, name='teacher_home'),
    path("teacher/apply/leave/", teacher_views.teacher_apply_leave,name='teacher_apply_leave'),
    path("teacher/view/profile/", teacher_views.teacher_view_profile,name='teacher_view_profile'),
    path("teacher/attendance/take/", teacher_views.teacher_take_attendance,name='teacher_take_attendance'),
    path("teacher/get_students/", teacher_views.get_students, name='get_students'),
    path("teacher/attendance/fetch/", teacher_views.get_student_attendance,name='get_student_attendance'),
    path("teacher/attendance/save/",teacher_views.save_attendance, name='save_attendance'),
    # path("teacher/attendance/update/",teacher_views.update_attendance, name='update_attendance'),
    path('get_attendance_students/', teacher_views.get_attendance_students, name='get_attendance_students'),
    path('teacher/attendance/manage/', teacher_views.teacher_manage_attendance, name='teacher_manage_attendance'),
    path('teacher/view_attendance/', teacher_views.teacher_view_attendance, name='teacher_view_attendance'),
    path('teacher/attendance/edit/<int:attendance_id>/', teacher_views.teacher_edit_attendance, name='teacher_edit_attendance'),
    path('teacher/attendance/delete/', teacher_views.teacher_delete_attendance, name='teacher_delete_attendance'),
    path("teacher/courses/", teacher_views.teacher_courses, name='teacher_courses'),
    path("teacher/fcmtoken/", teacher_views.teacher_fcmtoken, name='teacher_fcmtoken'),
    path("teacher/view/notification/", teacher_views.teacher_view_notification,name="teacher_view_notification"),
    path("teacher/view/notification/count/", teacher_views.teacher_view_notification_count, name="teacher_view_notification_count"),
    path('teacher/view/notification/read/<int:notification_id>/', teacher_views.mark_notification_as_read, name='mark_notification_as_read'),
    path('teacher/delete/notification/', teacher_views.teacher_delete_notification, name='teacher_delete_notification'),
    path("teacher/view/reminder/", teacher_views.teacher_view_reminder, name="teacher_view_reminder"),
    path("teacher/view/reminder/count/", teacher_views.teacher_view_reminder_count, name="teacher_view_reminder_count"),
    path('teacher/view/reminder/read/<int:reminder_id>/', teacher_views.mark_reminder_as_read, name='mark_reminder_as_read'),
    path('teacher/delete/reminder/', teacher_views.teacher_delete_reminder, name='teacher_delete_reminder'),
    path("teacher/write/summary/", teacher_views.teacher_write_summary, name='teacher_write_summary'),
    # path('teacher/delete/summary/', teacher_views.delete_summary, name='delete_summary'),
    # path("teacher/result/add/", teacher_views.teacher_add_result, name='teacher_add_result'),
    # path("teacher/result/edit/", teacher_views.teacher_edit_result,name='edit_student_result'),
    # path('teacher/result/fetch/', teacher_views.fetch_student_result,name='fetch_student_result'),
   

    
    # Student
    path("student/home/", student_views.student_home, name='student_home'),
    path("student/payment/", student_views.student_payment_records, name = "student_payment_records"),
    path("student/view/attendance/", student_views.student_view_attendance,name='student_view_attendance'),
    path("student/apply/leave/", student_views.student_apply_leave,name='student_apply_leave'),
    # path("student/summary/", student_views.student_summary,name='student_summary'),
    path("student/view/profile/", student_views.student_view_profile,name='student_view_profile'),
    path("student/fcmtoken/", student_views.student_fcmtoken,name='student_fcmtoken'),
    path("student/view/notification/", student_views.student_view_notification,name="student_view_notification"),
    path('student/view/result/', student_views.student_view_result,name='student_view_result'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



