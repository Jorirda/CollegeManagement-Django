
import json
from django.conf import settings
import requests
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.decorators.csrf import csrf_exempt
from .EmailBackend import EmailBackend
from .models import Attendance, Session, Classes
from django.shortcuts import redirect
from django.utils.translation import activate, LANGUAGE_SESSION_KEY


# Create your views here.


def switch_language(request):
    if 'lang' in request.GET:
        language = request.GET['lang']
        if language in [lang[0] for lang in settings.LANGUAGES]:
            request.session[LANGUAGE_SESSION_KEY] = language
            activate(language)
    return redirect(request.META.get('HTTP_REFERER', '/'))


def login_page(request):
    if request.user.is_authenticated:
        if request.user.user_type == '1':
            return redirect(reverse("admin_home"))
        elif request.user.user_type == '2':
            return redirect(reverse("teacher_home"))
        else:
            return redirect(reverse("student_home"))
    return render(request, 'main_app/login.html')


# def doLogin(request, **kwargs):
#     if request.method != 'POST':
#         return HttpResponse("<h4>Denied</h4>")
#     else:
#         # #Google recaptcha
#         # captcha_token = request.POST.get('g-recaptcha-response')
#         # captcha_url = "https://www.google.com/recaptcha/api/siteverify"
#         # captcha_key = "6LfswtgZAAAAABX9gbLqe-d97qE2g1JP8oUYritJ"
#         # data = {
#         #     'secret': captcha_key,
#         #     'response': captcha_token
#         # }
#         # # Make request
#         # try:
#         #     captcha_server = requests.post(url=captcha_url, data=data)
#         #     response = json.loads(captcha_server.text)
#         #     if response['success'] == False:
#         #         messages.error(request, 'Invalid Captcha. Try Again')
#         #         return redirect('/')
#         # except:
#         #     messages.error(request, 'Captcha could not be verified. Try Again')
#         #     return redirect('/')
        
#         #Authenticate
#         user = EmailBackend.authenticate(request, username=request.POST.get('email'), password=request.POST.get('password'))
#         if user != None:
#             login(request, user)
#             if user.user_type == '1':
#                 return redirect(reverse("admin_home"))
#             elif user.user_type == '2':
#                 return redirect(reverse("teacher_home"))
#             else:
#                 return redirect(reverse("student_home"))
#         else:
#             messages.error(request, "Invalid details")
#             return redirect("/")

from django.views.decorators.csrf import csrf_protect

@csrf_protect
def doLogin(request, **kwargs):
    if request.method != 'POST':
        return HttpResponse("<h4>Denied</h4>")
    else:
        # Print CSRF token for debugging
        csrf_token = request.POST.get('csrfmiddlewaretoken')
        print(f"CSRF Token from request: {csrf_token}")
        
        # Authenticate user
        user = EmailBackend.authenticate(request, username=request.POST.get('email'), password=request.POST.get('password'))
        if user is not None:
            login(request, user)
            if user.user_type == '1':
                return redirect(reverse("admin_home"))
            elif user.user_type == '2':
                return redirect(reverse("teacher_home"))
            else:
                return redirect(reverse("student_home"))
        else:
            messages.error(request, "Invalid details")
            return redirect("/")



def logout_user(request):
    if request.user != None:
        logout(request)
    return redirect("/")


@csrf_exempt
def get_attendance(request):
    classes_id = request.POST.get('classes')
    session_id = request.POST.get('session')
    try:
        classes = get_object_or_404(Classes, id=classes_id)
        session = get_object_or_404(Session, id=session_id)
        attendance = Attendance.objects.filter(classes=classes, session=session)
        attendance_list = []
        for attd in attendance:
            data = {
                    "id": attd.id,
                    "attendance_date": str(attd.date),
                    "session": attd.session.id
                    }
            attendance_list.append(data)
        return JsonResponse(json.dumps(attendance_list), safe=False)
    except Exception as e:
        return None


def showFirebaseJS(request):
    data = """
    // Give the service worker access to Firebase Messaging.
// Note that you can only use Firebase Messaging here, other Firebase libraries
// are not available in the service worker.
importScripts('https://www.gstatic.com/firebasejs/7.22.1/firebase-app.js');
importScripts('https://www.gstatic.com/firebasejs/7.22.1/firebase-messaging.js');

// Initialize the Firebase app in the service worker by passing in
// your app's Firebase config object.
// https://firebase.google.com/docs/web/setup#config-object
firebase.initializeApp({
    apiKey: "AIzaSyBarDWWHTfTMSrtc5Lj3Cdw5dEvjAkFwtM",
    authDomain: "sms-with-django.firebaseapp.com",
    databaseURL: "https://sms-with-django.firebaseio.com",
    projectId: "sms-with-django",
    storageBucket: "sms-with-django.appspot.com",
    messagingSenderId: "945324593139",
    appId: "1:945324593139:web:03fa99a8854bbd38420c86",
    measurementId: "G-2F2RXTL9GT"
});

// Retrieve an instance of Firebase Messaging so that it can handle background
// messages.
const messaging = firebase.messaging();
messaging.setBackgroundMessageHandler(function (payload) {
    const notification = JSON.parse(payload);
    const notificationOption = {
        body: notification.body,
        icon: notification.icon
    }
    return self.registration.showNotification(payload.notification.title, notificationOption);
});
    """
    return HttpResponse(data, content_type='application/javascript')
