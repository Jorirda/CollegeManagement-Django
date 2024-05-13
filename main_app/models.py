from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import UserManager
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db import IntegrityError, models
from django.contrib.auth.models import AbstractUser
from datetime import datetime, timedelta, date
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum



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

    username = None # Removed username, using email instead
    full_name = models.TextField(default="")
    email = models.EmailField(unique=True)
    user_type = models.CharField(default=1, choices=USER_TYPE, max_length=1)
    gender = models.CharField(max_length=1, choices=GENDER)
    profile_pic = models.ImageField()
    address = models.TextField(default="")
    phone_number = models.TextField(default="")
    remark = models.TextField(default="")
    fcm_token = models.TextField(default="")  # For firebase notifications
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    def __str__(self):
        return self.full_name

class Campus(models.Model):
    name = models.CharField(max_length=100)
    # institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='campuses')

    def __str__(self):
        return self.name

class Admin(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    remark = models.TextField(default="")

    def __str__(self):
        return str(self.admin)
class Course(models.Model):
    name = models.CharField(max_length=120)
    overview = models.TextField(default="")
    level_start = models.IntegerField(default=1)
    level_end = models.IntegerField(default=4)

    def __str__(self):
        return self.name

class Student(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, null=True)  
    course = models.ForeignKey(Course, on_delete=models.DO_NOTHING, null=True, blank=False)
    date_of_birth = models.DateField(blank=True, null=True)
    reg_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=30, blank=True) 

    def __str__(self):
        return self.admin.full_name

class Teacher(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.DO_NOTHING, null=True, blank=False)
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, null=True)  
    work_type = models.CharField(max_length=30, blank=True)  # Special/Temporary

    def __str__(self):
        return self.admin.full_name

#Learning Record

class Classes(models.Model):
    name = models.CharField(max_length=120)
    teacher = models.ForeignKey(Teacher,on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class ClassSchedule(models.Model):
    course = models.ForeignKey(Course, null=True, on_delete=models.CASCADE)
    lesson_unit_price = models.DecimalField(max_digits=10,default=0, decimal_places=2)
    teacher = models.ForeignKey(Teacher,null=True, on_delete=models.CASCADE)
    grade = models.CharField(max_length=3, blank=True,null=True)  
    start_time = models.TimeField(null=True)
    end_time = models.TimeField(null=True)
    lesson_hours = models.CharField(max_length=10, null=True)
    remark = models.TextField(default="")

class LearningRecord(models.Model):
    date = models.DateField()
    student = models.ForeignKey(Student, null=True, on_delete=models.DO_NOTHING)
    course = models.ForeignKey(Course, null=True, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, null=True, on_delete=models.CASCADE)
    schedule = models.ForeignKey(ClassSchedule, null=True, on_delete=models.CASCADE)
    start_time = models.TimeField(null=True)  # Add start_time field
    end_time = models.TimeField(null=True)    # Add end_time field
    lesson_hours = models.CharField(max_length=10, null=True)  # Add lesson_hours field

    def __str__(self):
        return f'{self.student} - {self.course} - {self.date}'


class Attendance(models.Model):
    session = models.ForeignKey(Session, on_delete=models.DO_NOTHING)
    classes = models.ForeignKey(Classes, on_delete=models.DO_NOTHING)
    date = models.DateField()

class AttendanceReport(models.Model):
    student = models.ForeignKey(Student, on_delete=models.DO_NOTHING)
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE)
    status = models.BooleanField(default=False)

class LeaveReportStudent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.CharField(max_length=60)
    message = models.TextField()
    status = models.SmallIntegerField(default=0)

class LeaveReportTeacher(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    date = models.CharField(max_length=60)
    message = models.TextField()
    status = models.SmallIntegerField(default=0)

class FeedbackStudent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    feedback = models.TextField()
    reply = models.TextField()

class FeedbackTeacher(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    feedback = models.TextField()
    reply = models.TextField()

class NotificationTeacher(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    message = models.TextField()

class NotificationStudent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    message = models.TextField()


class StudentResult(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    classes = models.ForeignKey(Classes, on_delete=models.CASCADE)
    test = models.FloatField(default=0)
    exam = models.FloatField(default=0)


#Payment Record
class PaymentRecord(models.Model):
    date = models.DateField()
    # next_payment_date = models.DateField()
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    lesson_unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2)
    book_costs = models.DecimalField(max_digits=10, decimal_places=2)
    other_fee = models.DecimalField(max_digits=10, decimal_places=2)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    payee = models.CharField(max_length=255)
    remark = models.TextField(default="")
    lesson_hours = models.DecimalField(max_digits=10, default=0, decimal_places=2)
    learning_record = models.OneToOneField(
        LearningRecord, 
        null=True, 
        related_name='payment_record', 
        on_delete=models.SET_NULL
    )

# class LessonHours(models.Model):
#     learning_record = models.ForeignKey(LearningRecord, on_delete=models.CASCADE)
#     hours = models.DecimalField(max_digits=10, decimal_places=2)


#Refund page
class RefundRecord(models.Model):
    # admin = models.OneToOneField(CustomUser, null=True, on_delete=models.CASCADE)
    student = models.ForeignKey(Student,null=True, on_delete=models.CASCADE)
    learning_records = models.ForeignKey(LearningRecord, null=True, on_delete=models.CASCADE)
    payment_records = models.ForeignKey(PaymentRecord,null=True, on_delete=models.CASCADE)
    refund_amount = models.DecimalField(max_digits=10,null=True, decimal_places=2)
    amount_refunded = models.DecimalField(max_digits=10,null=True, decimal_places=2)
    refund_reason = models.TextField(null=True,)

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

        student_query.paid_class_hours =  (student_query.payment_records.lesson_hours)
        
        # Retrieve the student's learning records as a queryset
        learning_records_query = LearningRecord.objects.filter(student=student)

        # Aggregate the total lesson hours
        total_lesson_hours = learning_records_query.aggregate(Sum('lesson_hours'))['lesson_hours__sum'] or 0
        total_lesson_hours = int(total_lesson_hours)  # Convert to int, truncating decimals

        # Use the aggregated hours in your calculation
        attendance_count = AttendanceReport.objects.filter(student_id=student_query.pk).count()
        student_query.remaining_hours = student_query.paid_class_hours - (total_lesson_hours * attendance_count)
        student_query.completed_hours = (total_lesson_hours * attendance_count)
        
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
            class_duration = datetime.combine(datetime.today(), record.end_time) - datetime.combine(datetime.today(), record.start_time)
            total_class_duration += class_duration

        # Count the number of courses and classess
        # num_of_courses = teacher.learningrecord_set.values('course').distinct().count()
        # num_of_classess = teacher.learningrecord_set.values('class_name').distinct().count()

        # Update the fields in TeacherQuery instance
        # teacher_query.num_of_classes = num_of_classess

        # Update the completed hours and remaining hours fields in TeacherQuery
        teacher_query.completed_hours = total_class_duration.total_seconds() // 3600  # Convert seconds to hours
        # teacher_query.remaining_hours = (num_of_classess * 2) - teacher_query.completed_hours  # Assuming each class is 30 hours

        # Save the updated StudentQuery instance
        teacher_query.save()

# Register signal handlers
post_save.connect(create_or_update_teacher_query, sender=Teacher)


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
