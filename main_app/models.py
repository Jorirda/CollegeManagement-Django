from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import UserManager
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db import IntegrityError, models
from django.contrib.auth.models import AbstractUser
from datetime import datetime, timedelta
from django.utils.translation import gettext_lazy as _


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
    home_number = models.TextField(default="")
    cell_number = models.TextField(default="")
    campus = models.CharField(max_length=100, blank=True)
    grade = models.CharField(max_length=10, blank=True)
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
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
class Campus(models.Model):
    name = models.CharField(max_length=100)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='campuses')

    def __str__(self):
        return self.name
class Admin(models.Model):
    admin = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    remark = models.TextField(default="")

    def __str__(self):
        return str(self.admin)

class Course(models.Model):
    name = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Student(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    institution = models.ForeignKey(Institution, on_delete=models.DO_NOTHING, null=True, blank=False, related_name='student_institutions')
    course = models.ForeignKey(Course, on_delete=models.DO_NOTHING, null=True, blank=False)
    session = models.ForeignKey(Session, on_delete=models.DO_NOTHING, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    reg_date = models.DateField(blank=True, null=True)
    state = models.CharField(max_length=30, blank=True)  # learning/completed/pending refund

    def __str__(self):
        return self.admin.last_name + ", " + self.admin.first_name


class Teacher(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.DO_NOTHING, null=True, blank=False, related_name='teacher_institutions')
    course = models.ForeignKey(Course, on_delete=models.DO_NOTHING, null=True, blank=False)
    campus = models.ForeignKey(Campus, on_delete=models.DO_NOTHING, null=True, blank=True)  # Make it nullable
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    work_type = models.CharField(max_length=30, blank=True)  # Special/Temporary

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
    status = models.CharField(max_length=100)
    payee = models.CharField(max_length=255)
    remark = models.TextField(default="")


#Learning Record
class LearningRecord(models.Model):
    date = models.DateField()
    student = models.ForeignKey(Student, null=True,on_delete=models.DO_NOTHING)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, null=True)
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, null=True)  
    course = models.ForeignKey(Course,null=True, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher,null=True, on_delete=models.CASCADE)
    starting_time = models.TimeField(null=True,)
    end_time = models.TimeField(null=True,)
    class_name = models.CharField(max_length=100, null=True,)
    remark = models.TextField(null=True,)

#Class Schedule
class ClassSchedule(models.Model):
    course = models.ForeignKey(Course, null=True, on_delete=models.CASCADE)
    lesson_unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    teacher = models.ForeignKey(Teacher,null=True, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject,null=True, on_delete=models.DO_NOTHING)
    class_time = models.CharField(max_length=100)
    remark = models.TextField(default="")


    def lesson_unit_price(self):
        # Fetch the related PaymentRecord for this ClassSchedule
        payment_record = PaymentRecord.objects.filter(course=self.course).first()

        # Return the lesson_unit_price if PaymentRecord exists, otherwise return
        #
        # None
        return payment_record.lesson_unit_price if payment_record else None

class StudentQuery(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]

    admin = models.OneToOneField(CustomUser, null=True, on_delete=models.CASCADE)
    student_records = models.ForeignKey(Student, null=True, on_delete=models.CASCADE)
    payment_records = models.ForeignKey(PaymentRecord, null=True, on_delete=models.CASCADE)
    refund = models.CharField(max_length=100, null=True, default='Pending')  # Default value for refund
    num_of_classes = models.IntegerField(null=True, default=0)  # Default value for num_of_classes
    registered_courses = models.CharField(max_length=100, null=True, default='')  # Default value for registered_courses
    completed_hours = models.IntegerField(null=True, default=0)  # Default value for completed_hours
    paid_class_hours = models.IntegerField(null=True, default=0)  # Default value for paid_class_hours
    remaining_hours = models.IntegerField(null=True, default=0)  # Default value for remaining_hours
    learning_records = models.ForeignKey(LearningRecord, null=True, on_delete=models.CASCADE)

class TeacherQuery(models.Model):
    admin = models.OneToOneField(CustomUser, null=True, on_delete=models.CASCADE)
    teacher_records = models.ForeignKey(Teacher, null=True, on_delete=models.CASCADE)
    learning_records = models.ForeignKey(LearningRecord, null=True, on_delete=models.CASCADE)
    num_of_classes = models.IntegerField(null=True)
    completed_hours = models.IntegerField(null=True)
    remaining_hours = models.IntegerField(null=True, default=0)  # Default value for remaining_hours

@receiver(post_save, sender=Student)
@receiver(post_save, sender=LearningRecord)
@receiver(post_save, sender=PaymentRecord)
def create_or_update_student_query(sender, instance, created, **kwargs):
    student = None
    if isinstance(instance, Student):
        student = instance
    elif isinstance(instance, LearningRecord) or isinstance(instance, PaymentRecord):
        student = instance.student

    if student:
        # Ensure only one StudentQuery is associated with each student, handle creation or update
        student_query, created = StudentQuery.objects.get_or_create(student_records=student)

        if isinstance(instance, Student):
            print("Student instance saved or updated.")
        elif isinstance(instance, LearningRecord):
            print("LearningRecord instance saved or updated, associated with student.")
        elif isinstance(instance, PaymentRecord):
            print("PaymentRecord instance saved or updated, associated with student.")

        # Get related learning and payment records
        related_learning_records = student.learningrecord_set.all()
        related_payment_records = student.paymentrecord_set.all()

        # Get the first instance safely
        learning_record_instance = related_learning_records.first()
        payment_record_instance = related_payment_records.first()

        if learning_record_instance:
            student_query.learning_records = learning_record_instance

        if payment_record_instance:
            student_query.payment_records = payment_record_instance

        # Assuming you want to save the student_query after modifications
        try:
            student_query.save()
            print(f"StudentQuery for {student} updated successfully.")
        except IntegrityError as e:
            print(f"Error saving StudentQuery for {student}: {str(e)}")
# Register signal handlers
post_save.connect(create_or_update_student_query, sender=Student)

@receiver(post_save, sender=Teacher)
@receiver(post_save, sender=LearningRecord)
def create_or_update_teacher_query(sender, instance, created, **kwargs):
    """
    Signal handler for creating or updating TeacherQuery instance when a Teacher instance is created or updated.
    """
    teacher = None
    if isinstance(instance, Teacher):
        teacher = instance
        print("Teacher")
    elif isinstance(instance, LearningRecord):
        teacher = instance.teacher
        print("Teaching")
   
    if teacher:
        try:
            # Attempt to retrieve the existing TeacherQuery instance related to the teacher
            teacher_query = TeacherQuery.objects.get(teacher_records=teacher)
        except TeacherQuery.DoesNotExist:
            # If TeacherQuery instance does not exist, create a new one
            teacher_query = TeacherQuery.objects.create(teacher_records=teacher)

    # Update the fields of the TeacherQuery instance
        teacher_query.admin = teacher.admin
       
        # Get related learning records 
        related_learning_records = teacher.learningrecord_set.all()
       
        # Update learning records fields in TeacherQuery
        learning_record_instance = related_learning_records.first()
        
        if learning_record_instance:
            teacher_query.learning_records = learning_record_instance

        # Set learning record id
        teacher_query.learning_record_id = learning_record_instance.id if learning_record_instance else None

        # Calculate class duration for learning records
        total_class_duration = timedelta()  # Initialize total class duration as timedelta object
        for record in related_learning_records:
            class_duration = datetime.combine(datetime.today(), record.end_time) - datetime.combine(datetime.today(), record.starting_time)
            total_class_duration += class_duration

        # Count the number of courses and subjects
        # num_of_courses = teacher.learningrecord_set.values('course').distinct().count()
        num_of_subjects = teacher.learningrecord_set.values('class_name').distinct().count()

        # Update the fields in TeacherQuery instance
        teacher_query.num_of_classes = num_of_subjects

        # Update the completed hours and remaining hours fields in TeacherQuery
        teacher_query.completed_hours = total_class_duration.total_seconds() // 3600  # Convert seconds to hours
        teacher_query.remaining_hours = (num_of_subjects * 2) - teacher_query.completed_hours  # Assuming each class is 30 hours

        # Save the updated StudentQuery instance
        teacher_query.save()

# Register signal handlers
post_save.connect(create_or_update_teacher_query, sender=Teacher)

# TeacherQuery here
# class TeacherQuery(models.Model):
#     GENDER_CHOICES = [
#         ('M', 'Male'),
#         ('F', 'Female'),
#     ]

#     admin = models.OneToOneField(CustomUser,null = True, on_delete=models.CASCADE)
#     num_of_classes = models.IntegerField(null = True)
#     registered_courses = models.CharField(max_length=100, null=True)
#     completed_hours = models.IntegerField(null = True)
#     paid_class_hours = models.IntegerField(null = True)
#     remaining_hours = models.IntegerField(null = True)

#     learning_records = models.ForeignKey(LearningRecord, null=True,on_delete=models.CASCADE)





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
