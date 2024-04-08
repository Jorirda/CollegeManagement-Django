from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *
# Register your models here.


class UserModel(UserAdmin):
    ordering = ('email',)


admin.site.register(CustomUser, UserModel)
admin.site.register(Teacher)
admin.site.register(Student)
admin.site.register(Course)
admin.site.register(Subject)
admin.site.register(Session)
admin.site.register(StudentQuery)
admin.site.register(LearningRecord)
admin.site.register(PaymentRecord)
