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

from main_app.EditResultView import EditResultView

from . import hod_views, teacher_views, student_views, views

urlpatterns = [
    path("", views.login_page, name='login_page'),
    path("get_attendance", views.get_attendance, name='get_attendance'),
    path("firebase-messaging-sw.js", views.showFirebaseJS, name='showFirebaseJS'),
    path("doLogin/", views.doLogin, name='user_login'),
    path("logout_user/", views.logout_user, name='user_logout'),
    path("admin/home/", hod_views.admin_home, name='admin_home'),
    path("teacher/query", hod_views.view_teacher_query, name='view_teacher_query'),
    path("teacher/add", hod_views.add_teacher, name='add_teacher'),
    path("course/add", hod_views.add_course, name='add_course'),
    path("send_student_notification/", hod_views.send_student_notification,
         name='send_student_notification'),
    path("send_teacher_notification/", hod_views.send_teacher_notification,
         name='send_teacher_notification'),
    path("add_session/", hod_views.add_session, name='add_session'),
    path("admin_notify_student", hod_views.admin_notify_student,
         name='admin_notify_student'),
    path("admin_notify_teacher", hod_views.admin_notify_teacher,
         name='admin_notify_teacher'),
    path("admin_view_profile", hod_views.admin_view_profile,
         name='admin_view_profile'),
    path("check_email_availability", hod_views.check_email_availability,
         name="check_email_availability"),
    path("session/manage/", hod_views.manage_session, name='manage_session'),
    path("session/edit/<int:session_id>",
         hod_views.edit_session, name='edit_session'),
    path("student/view/feedback/", hod_views.student_feedback_message,
         name="student_feedback_message",),
    path("teacher/view/feedback/", hod_views.teacher_feedback_message,
         name="teacher_feedback_message",),
    path("student/view/leave/", hod_views.view_student_leave,
         name="view_student_leave",),
    path("teacher/view/leave/", hod_views.view_teacher_leave, name="view_teacher_leave",),
    path("attendance/view/", hod_views.admin_view_attendance,
         name="admin_view_attendance",),
    path("attendance/fetch/", hod_views.get_admin_attendance,
         name='get_admin_attendance'),
    path("student/query/", hod_views.view_student_query, name = "view_student_query"),
    path("student/add/", hod_views.add_student, name='add_student'),
    path("subject/add/", hod_views.add_subject, name='add_subject'),
    path("teacher/manage/", hod_views.manage_teacher, name='manage_teacher'),
    path("student/manage/", hod_views.manage_student, name='manage_student'),
    path("course/manage/", hod_views.manage_course, name='manage_course'),
    path("subject/manage/", hod_views.manage_subject, name='manage_subject'),
    path("teacher/edit/<int:teacher_id>", hod_views.edit_teacher, name='edit_teacher'),
    path("teacher/delete/<int:teacher_id>",
         hod_views.delete_teacher, name='delete_teacher'),

    path("course/delete/<int:course_id>",
         hod_views.delete_course, name='delete_course'),

    path("subject/delete/<int:subject_id>",
         hod_views.delete_subject, name='delete_subject'),

    path("session/delete/<int:session_id>",
         hod_views.delete_session, name='delete_session'),

    path("student/delete/<int:student_id>",
         hod_views.delete_student, name='delete_student'),
    path("student/edit/<int:student_id>",
         hod_views.edit_student, name='edit_student'),
    path("course/edit/<int:course_id>",
         hod_views.edit_course, name='edit_course'),
    path("subject/edit/<int:subject_id>",
         hod_views.edit_subject, name='edit_subject'),


    # teacher
    path("teacher/home/", teacher_views.teacher_home, name='teacher_home'),
    path("teacher/apply/leave/", teacher_views.teacher_apply_leave,
         name='teacher_apply_leave'),
    path("teacher/feedback/", teacher_views.teacher_feedback, name='teacher_feedback'),
    path("teacher/view/profile/", teacher_views.teacher_view_profile,
         name='teacher_view_profile'),
    path("teacher/attendance/take/", teacher_views.teacher_take_attendance,
         name='teacher_take_attendance'),
    path("teacher/attendance/update/", teacher_views.teacher_update_attendance,
         name='teacher_update_attendance'),
    path("teacher/get_students/", teacher_views.get_students, name='get_students'),
    path("teacher/attendance/fetch/", teacher_views.get_student_attendance,
         name='get_student_attendance'),
    path("teacher/attendance/save/",
         teacher_views.save_attendance, name='save_attendance'),
    path("teacher/attendance/update/",
         teacher_views.update_attendance, name='update_attendance'),
    path("teacher/fcmtoken/", teacher_views.teacher_fcmtoken, name='teacher_fcmtoken'),
    path("teacher/view/notification/", teacher_views.teacher_view_notification,
         name="teacher_view_notification"),
    path("teacher/result/add/", teacher_views.teacher_add_result, name='teacher_add_result'),
    path("teacher/result/edit/", EditResultView.as_view(),
         name='edit_student_result'),
    path('teacher/result/fetch/', teacher_views.fetch_student_result,
         name='fetch_student_result'),



    # Student
    path("student/home/", student_views.student_home, name='student_home'),
    path("student/payment/", student_views.student_payment_records, name = "student_payment_records"),
    path("student/view/attendance/", student_views.student_view_attendance,
         name='student_view_attendance'),
    path("student/apply/leave/", student_views.student_apply_leave,
         name='student_apply_leave'),
    path("student/feedback/", student_views.student_feedback,
         name='student_feedback'),
    path("student/view/profile/", student_views.student_view_profile,
         name='student_view_profile'),
    path("student/fcmtoken/", student_views.student_fcmtoken,
         name='student_fcmtoken'),
    path("student/view/notification/", student_views.student_view_notification,
         name="student_view_notification"),
    path('student/view/result/', student_views.student_view_result,
         name='student_view_result'),

]
