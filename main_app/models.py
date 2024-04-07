from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import UserManager
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db import models
from django.contrib.auth.models import AbstractUser




class CustomUserManager(UserManager):
    def _create_user(self, email, password, **extra_fields):
        email = self.normalize_email(email)
        user = CustomUser(email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_teacher", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_teacher", True)
        extra_fields.setdefault("is_superuser", True)

        assert extra_fields["is_teacher"]
        assert extra_fields["is_superuser"]
        return self._create_user(email, password, **extra_fields)


class Session(models.Model):
    start_year = models.DateField()
    end_year = models.DateField()

    def __str__(self):
        return "From " + str(self.start_year) + " to " + str(self.end_year)


class CustomUser(AbstractUser):
    USER_TYPE = ((1, "HOD"), (2, "Teacher"), (3, "Student"))
    GENDER = [("M", "Male"), ("F", "Female")]
    
    
    username = None  # Removed username, using email instead
    email = models.EmailField(unique=True)
    user_type = models.CharField(default=1, choices=USER_TYPE, max_length=1)
    gender = models.CharField(max_length=1, choices=GENDER)
    profile_pic = models.ImageField()
    address = models.TextField()
    contact_num = models.TextField(default="")
    remark = models.TextField(default="")
    fcm_token = models.TextField(default="")  # For firebase notifications
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    def __str__(self):
        return self.last_name + ", " + self.first_name


#Institution
class Institution(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
   
    
#Campus
class Campus(models.Model):
    id = models.AutoField(primary_key=True)
    institution = models.ForeignKey('Institution', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
   
class Admin(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)



class Course(models.Model):
    name = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Student(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.DO_NOTHING, null=True, blank=False)
    session = models.ForeignKey(Session, on_delete=models.DO_NOTHING, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    reg_date = models.DateField(blank=True, null=True)
    state = models.CharField(max_length = 30, blank = True) #learning/completed/pending refund
    
    def __str__(self):
        return self.admin.last_name + ", " + self.admin.first_name


class Teacher(models.Model):
    course = models.ForeignKey(Course, on_delete=models.DO_NOTHING, null=True, blank=False)
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    work_type = models.CharField(max_length = 30, blank = True) #Special/Temporary
    
    def __str__(self):
        return self.admin.last_name + " " + self.admin.first_name


class Subject(models.Model):
    name = models.CharField(max_length=120)
    teacher = models.ForeignKey(Teacher,on_delete=models.CASCADE,)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Attendance(models.Model):
    session = models.ForeignKey(Session, on_delete=models.DO_NOTHING)
    subject = models.ForeignKey(Subject, on_delete=models.DO_NOTHING)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class AttendanceReport(models.Model):
    student = models.ForeignKey(Student, on_delete=models.DO_NOTHING)
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE)
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LeaveReportStudent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.CharField(max_length=60)
    message = models.TextField()
    status = models.SmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LeaveReportTeacher(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    date = models.CharField(max_length=60)
    message = models.TextField()
    status = models.SmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FeedbackStudent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    feedback = models.TextField()
    reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FeedbackTeacher(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    feedback = models.TextField()
    reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class NotificationTeacher(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class NotificationStudent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class StudentResult(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    test = models.FloatField(default=0)
    exam = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


#Payment Record
class PaymentRecord(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.DateField()
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course,on_delete=models.CASCADE)
    lesson_unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    class_name = models.CharField(max_length=100)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2)
    book_costs = models.DecimalField(max_digits=10, decimal_places=2)
    other_fee = models.DecimalField(max_digits=10, decimal_places=2)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=100)
    payee = models.CharField(max_length=255)
    remark = models.TextField(default="")


#Learning Record
class LearningRecord(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.DateField()
    student = models.ForeignKey(Student, on_delete=models.DO_NOTHING)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    starting_time = models.TimeField()
    end_time = models.TimeField()
    class_name = models.CharField(max_length=100)
    remark = models.TextField(default="")

    

#Class Schedule
class ClassSchedule(models.Model):
    id = models.AutoField(primary_key=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    lesson_unit_price = models.CharField(max_length=100)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.DO_NOTHING)
    class_time = models.CharField(max_length=100)
    remark = models.TextField(default="")

class StudentQuery(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        
    ]

    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    state = models.CharField(max_length=100)
    payment_status = models.CharField(max_length=100)
    refund_situation = models.CharField(max_length=100)
    registration_date = models.DateField()
    number_of_classes = models.IntegerField()
    already_registered_for_courses = models.CharField(max_length=100)
    course_hours_completed = models.IntegerField()
    paid_class_hours = models.IntegerField()
    remaining_class_hours = models.IntegerField()

    def __str__(self):
        return f"{self.id} - {self.registration_date}"
    
class TeacherQuery(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]

    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    contact_number = models.CharField(max_length=100)
    teaching_courses = models.CharField(max_length=100)
    signing_form = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    course_hours_completed = models.IntegerField(default=0)
    number_of_classes = models.IntegerField(default=0)
    class_schedule_date = models.DateField()
    class_schedule_course = models.CharField(max_length=100)
    class_schedule_instructor = models.CharField(max_length=100)
    class_schedule_starting_time = models.TimeField()
    class_schedule_end_time = models.TimeField()
    class_schedule_class = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.id} - {self.class_schedule_date}"




@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.user_type == 1:
            Admin.objects.create(admin=instance)
        if instance.user_type == 2:
            Teacher.objects.create(admin=instance)
        if instance.user_type == 3:
            Student.objects.create(admin=instance)


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    if instance.user_type == 1:
        instance.admin.save()
    if instance.user_type == 2:
        instance.teacher.save()
    if instance.user_type == 3:
        instance.student.save()
