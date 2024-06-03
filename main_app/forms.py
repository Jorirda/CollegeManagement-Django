from django import forms
from django.forms.widgets import DateInput, TextInput, TimeInput
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import gettext_lazy as _
from .models import *

class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField()
    model = forms.ChoiceField(
        choices=[('', 'Select Table Type'), ('CustomUser', 'CustomUser'), ('Session', 'Session'), ('Campus', 'Campus'),
                 ('Course', 'Course'), ('ClassSchedule', 'ClassSchedule'), ('LearningRecord', 'LearningRecord'),
                 ('PaymentRecord', 'PaymentRecord'), ('RefundRecord', 'RefundRecord'), ('Mixed', 'Mixed')],
        required=True
    )
    user_type = forms.ChoiceField(
        choices=[('Teacher', 'Teacher'), ('Student', 'Student')],
        required=False,
        widget=forms.RadioSelect
    )

class FormSettings(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormSettings, self).__init__(*args, **kwargs)
        for field in self.visible_fields():
            # Apply form-control class to all fields except checkboxes
            if isinstance(field.field.widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                field.field.widget.attrs['class'] = 'form-check-input'
            else:
                field.field.widget.attrs['class'] = 'form-control'

class CustomUserForm(FormSettings):
    full_name = forms.CharField(required=True, label=_('Full Name'))
    email = forms.EmailField(required=True, label=_('Email'))
    gender = forms.ChoiceField(choices=[('male', _('Male')), ('female', _('Female'))], label=_('Gender'))
    password = forms.CharField(widget=forms.PasswordInput, label=_('Password'))
    profile_pic = forms.ImageField(label=_('Profile Picture')) 
    address = forms.CharField(widget=forms.Textarea, label=_('Address'))
    phone_number = forms.CharField(max_length=20, required=False, label=_("Phone Number"))
    remark = forms.CharField(required=True, label=_('Remark'))

    class Meta:
        model = CustomUser
        fields = ['full_name', 'email', 'gender', 'password', 'profile_pic', 'address', 'phone_number', 'remark']

    def __init__(self, *args, **kwargs):
        super(CustomUserForm, self).__init__(*args, **kwargs)
        if kwargs.get('instance'):
            instance = kwargs.get('instance').admin.__dict__
            self.fields['password'].required = False
            for field in CustomUserForm.Meta.fields:
                self.fields[field].initial = instance.get(field)
            if self.instance.pk is not None:
                self.fields['password'].widget.attrs['placeholder'] = _("Fill this only if you wish to update password")

    def clean_email(self, *args, **kwargs):
        formEmail = self.cleaned_data['email'].lower()
        if self.instance.pk is None:  # Insert
            if CustomUser.objects.filter(email=formEmail).exists():
                raise forms.ValidationError(_("The given email is already registered"))
        else:  # Update
            dbEmail = self.Meta.model.objects.get(id=self.instance.pk).admin.email.lower()
            if dbEmail != formEmail:  # There has been changes
                if CustomUser.objects.filter(email=formEmail).exists():
                    raise forms.ValidationError(_("The given email is already registered"))
        return formEmail

class StudentForm(CustomUserForm):
    full_name = forms.CharField(required=True, label=_('Full Name'))
    gender = forms.ChoiceField(choices=[('男', _('Male')), ('女', _('Female'))], label=_('Gender'))
    address = forms.CharField(widget=forms.Textarea, label=_('Address'))
    date_of_birth = forms.DateField(required=False, label=_("Date of Birth"), widget=forms.DateInput(attrs={'type': 'date', 'class': 'hideable'}))
    reg_date = forms.DateField(required=False, label=_("Registration Date"), widget=forms.DateInput(attrs={'type': 'date', 'class': 'hideable'}))
    status = forms.ChoiceField(choices=[  
        ('Currently Learning', _('Currently Learning')),
        ('Completed', _('Completed')),
        ('Refund', _('Refund')),
    ], label=_("Status"), widget=forms.Select(attrs={'class': 'hideable'}))
    phone_number = forms.CharField(max_length=20, required=False, label=_("Phone Number"))
    remark = forms.CharField(required=False, label=_('Remark'))
    campus = forms.ModelChoiceField(queryset=Campus.objects.all(), required=False, label=_("Campus"))
    courses = forms.ModelMultipleChoiceField(
        queryset=Course.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'courses-field'}),
        label=_("Courses")
    )

    class Meta:
        model = Student
        fields = ['full_name', 'gender', 'address', 'date_of_birth', 'reg_date', 'status', 'phone_number', 'remark', 'campus', 'courses']

    def __init__(self, *args, **kwargs):
        super(StudentForm, self).__init__(*args, **kwargs)
        if self.instance.pk:  # if the instance exists (editing case)
            self.fields['campus'].initial = self.instance.campus
            self.fields['courses'].initial = self.instance.courses.all()
        # Reorder fields as requested
        field_order = [_('full_name'), _('gender'), _('date_of_birth'), _('address'), _('phone_number'), _('campus'), _('courses'),_('reg_date'), _('status'), _('remark'), ]
                         
        # Set the field order
        self.fields = {k: self.fields[k] for k in field_order}

    def save(self, commit=True):
        instance = super(StudentForm, self).save(commit=False)
        user = instance.admin
        user.full_name = self.cleaned_data['full_name']
        user.gender = self.cleaned_data['gender']
        user.address = self.cleaned_data['address']
        user.phone_number = self.cleaned_data['phone_number']
        user.remark = self.cleaned_data['remark']

        if commit:
            user.save()
            instance.save()
            instance.courses.set(self.cleaned_data['courses'])
        return instance

class AdminForm(FormSettings):
    full_name = forms.CharField(required=False, label=_('Full Name'))
    email = forms.EmailField(required=False, label=_('Email'))
    gender = forms.ChoiceField(choices=[('male', _('Male')), ('female', _('Female'))], label=_('Gender'))
    password = forms.CharField(widget=forms.PasswordInput, label=_('Password'), required=False)
    profile_pic = forms.ImageField(label=_('Profile Picture'))

    def __init__(self, *args, **kwargs):
        super(AdminForm, self).__init__(*args, **kwargs)
        if self.instance.pk:  # if the instance exists (editing case)
            self.fields['full_name'].initial = self.instance.admin.full_name
            self.fields['gender'].initial = self.instance.admin.gender
            self.fields['email'].initial = self.instance.admin.email
      
    def save(self, commit=True):
        instance = super(TeacherForm, self).save(commit=False)
        user = instance.admin
        user.full_name = self.cleaned_data['full_name']
        user.gender = self.cleaned_data['gender']
        user.email = self.cleaned_data['email']
        
        # Reorder fields as requested
        field_order = [_('full_name'), _('email'), _('gender'), _('password'), _('profile_pic')]

        # Set the field order
        self.fields = {k: self.fields[k] for k in field_order}

    class Meta:
        model = Admin
        fields = ['full_name', 'email', 'gender', 'password', 'profile_pic']

class TeacherForm(FormSettings):
    full_name = forms.CharField(required=True, label=_('Full Name'))
    gender = forms.ChoiceField(choices=[('男', _('Male')), ('女', _('Female'))], label=_('Gender'))
    email = forms.EmailField(widget=forms.EmailInput, label=_('Email'))
    password = forms.CharField(widget=forms.PasswordInput, required=False, label=_('Password'))
    address = forms.CharField(widget=forms.Textarea, label=_('Address'))
    phone_number = forms.CharField(max_length=20, required=False, label=_("Phone Number"))
    campus = forms.ModelChoiceField(queryset=Campus.objects.all(), required=False, label=_("Campus"))
    courses = forms.ModelMultipleChoiceField(
        queryset=Course.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'courses-field'}),
        label=_("Courses")
    )
    remark = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control remarks-field'}),
        required=False,
        label=_('Remark')
    )
    work_type = forms.ChoiceField(
        choices=[
            ('Full Time', _('Full Time')),
            ('Part Time', _('Part Time')),
        ],
        label=_("Contract"),
        widget=forms.Select(attrs={'class': 'form-control spaced-field'})
    )

    def __init__(self, *args, **kwargs):
        super(TeacherForm, self).__init__(*args, **kwargs)
        if self.instance.pk:  # if the instance exists (editing case)
            self.fields['full_name'].initial = self.instance.admin.full_name
            self.fields['gender'].initial = self.instance.admin.gender
            self.fields['email'].initial = self.instance.admin.email
            self.fields['address'].initial = self.instance.admin.address
            self.fields['phone_number'].initial = self.instance.admin.phone_number
            self.fields['remark'].initial = self.instance.admin.remark
            self.fields['courses'].initial = self.instance.courses.all()

    def save(self, commit=True):
        instance = super(TeacherForm, self).save(commit=False)
        user = instance.admin
        user.full_name = self.cleaned_data['full_name']
        user.gender = self.cleaned_data['gender']
        user.email = self.cleaned_data['email']
        user.address = self.cleaned_data['address']
        user.phone_number = self.cleaned_data['phone_number']
        user.remark = self.cleaned_data['remark']

        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)

        if commit:
            user.save()
            instance.save()
            instance.courses.set(self.cleaned_data['courses'])
        return instance
    
    class Meta:
        model = Teacher
        fields = ['full_name', 'gender', 'email', 'password', 'address', 'phone_number', 'campus', 'courses', 'work_type', 'remark']

class CourseForm(FormSettings):
    name = forms.CharField(label=_('Course Name'))
    overview = forms.CharField(label=_('Course Description'), widget=forms.Textarea)
    LEVEL_GRADE_CHOICES = [(str(i), chr(64 + i)) for i in range(1, 8)]
    # hourly_rate = forms.DecimalField(
    #     required=False,
    #     label=_("Hourly Rate"),
    #     widget=forms.NumberInput(attrs={'class': 'form-control'}),
    # )

    level_grade = forms.ChoiceField(
        choices=LEVEL_GRADE_CHOICES,
        label=_("Max Level"),
        help_text=_("Select a level, which corresponds to a grade.")
    )
    image = forms.ImageField(label=_('Course Image'), required=False)  # Add this line

    class Meta:
        model = Course
        fields = ['name', 'overview', 'level_grade', 'image']

class ClassesForm(FormSettings):
    name = forms.CharField(label=_('Classes Name'))
    teacher = forms.ModelChoiceField(queryset=Teacher.objects.all(), label=_('Teacher'))
    course = forms.ModelChoiceField(queryset=Course.objects.all(), label=_('Course'))
    def __init__(self, *args, **kwargs):
        super(ClassesForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Classes
        fields = [_('name'), _('teacher'), _('course')]

class CampusForm(FormSettings):
    name = forms.CharField(label=_('Name'))
    principal = forms.CharField(label=_('Principal'))  # New field
    principal_contact_number = forms.CharField(label=_('Principal Contact Number'))  # New field

    def __init__(self, *args, **kwargs):
        super(CampusForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Campus
        fields = ['name', 'principal', 'principal_contact_number']

class LearningRecordForm(FormSettings):
    date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}), label=_('Date'))
    student = forms.ModelChoiceField(queryset=Student.objects.all(), required=False, label=_("Name"))
    course = forms.ModelChoiceField(queryset=Course.objects.all(), required=False, label=_("Course"))
    teacher = forms.ModelChoiceField(queryset=Teacher.objects.none(), required=False, label=_("Teacher"))
    semester = forms.ModelChoiceField(queryset=Session.objects.all(), required=False, label=_("Semester"))
    day = forms.CharField(max_length=10, required=False, widget=forms.TextInput(attrs={'readonly': 'readonly'}), label=_('Day'))
    start_time = forms.TimeField(required=False, label=_("Start Time"), widget=forms.TimeInput(attrs={'readonly': 'readonly'}))
    end_time = forms.TimeField(required=False, label=_("End Time"), widget=forms.TimeInput(attrs={'readonly': 'readonly'}))
    lesson_hours = forms.DecimalField(required=False, max_digits=5, decimal_places=2, label=_("Lesson Hours"), widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}))

    class Meta:
        model = LearningRecord
        fields = ['date', 'student', 'course', 'teacher', 'day', 'start_time', 'end_time', 'lesson_hours', 'semester']

    def __init__(self, *args, **kwargs):
        super(LearningRecordForm, self).__init__(*args, **kwargs)
        self.fields['course'].queryset = Course.objects.all()

        if self.data:
            course_id = self.data.get('course')
            teacher_id = self.data.get('teacher')

            if course_id and teacher_id:
                course = Course.objects.get(id=course_id)
                teacher = Teacher.objects.get(id=teacher_id)
                schedule = ClassSchedule.objects.filter(course=course, teacher=teacher).first()

                if schedule:
                    self.fields['day'].initial = schedule.get_day_display()
                    self.fields['start_time'].initial = schedule.start_time
                    self.fields['end_time'].initial = schedule.end_time
                    self.fields['lesson_hours'].initial = schedule.lesson_hours

            if course_id:
                self.fields['teacher'].queryset = Teacher.objects.filter(courses__id=course_id)
            else:
                self.fields['teacher'].queryset = Teacher.objects.none()
        else:
            self.fields['teacher'].queryset = Teacher.objects.none()

    def save(self, commit=True):
        instance = super(LearningRecordForm, self).save(commit=False)
        course = self.cleaned_data.get('course')
        teacher = self.cleaned_data.get('teacher')

        if course and teacher:
            schedule = ClassSchedule.objects.filter(course=course, teacher=teacher).first()
            if schedule:
                instance.day = schedule.get_day_display()
                instance.start_time = schedule.start_time
                instance.end_time = schedule.end_time
                instance.lesson_hours = schedule.lesson_hours

        if commit:
            instance.save()
        return instance


class PaymentRecordForm(FormSettings):
    payee = forms.CharField(label=_('Payee'))
    remark = forms.CharField(required=True, label=_('Remark'))
    student = forms.ModelChoiceField(queryset=Student.objects.all(), required=False, label=_("Student"))
    course = forms.ModelChoiceField(queryset=Course.objects.all(), required=False, label=_("Course"))
    date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}), label=_('Date'))
    payment_method = forms.ChoiceField(choices=PaymentRecord.PAYMENT_METHOD_CHOICES, label=_('Payment Method'))
    status = forms.ChoiceField(choices=PaymentRecord.STATUS_CHOICES, label=_('Status'))
    lesson_unit_price = forms.DecimalField(widget=forms.TextInput(attrs={'placeholder': _('¥')}), label=_('Lesson Unit Price'))
    discounted_price = forms.DecimalField(widget=forms.TextInput(attrs={'placeholder': _('¥')}), label=_('Discounted Price'))
    book_costs = forms.DecimalField(widget=forms.TextInput(attrs={'placeholder': _('¥')}), label=_('Book Costs'))
    other_fee = forms.DecimalField(widget=forms.TextInput(attrs={'placeholder': _('¥')}), label=_('Other Fee'))
    amount_due = forms.DecimalField(widget=forms.TextInput(attrs={'placeholder': _('¥')}), label=_('Amount Due'))
    amount_paid = forms.DecimalField(widget=forms.TextInput(attrs={'placeholder': _('¥')}), label=_('Amount Paid'))
    lesson_hours = forms.DecimalField(widget=forms.TextInput(attrs={'readonly': 'readonly'}), required=False, label=_('Lesson Hours'))  # Changed to DecimalField

    class Meta:
        model = PaymentRecord
        fields = [
            'date', 'student', 'course', 'lesson_unit_price',
            'discounted_price', 'book_costs', 'other_fee', 'amount_due', 'amount_paid', 
            'payment_method', 'status', 'payee', 'remark', 'lesson_hours'  # Included lesson_hours in fields
        ]
class ClassScheduleForm(FormSettings):
    def get_level_grade_choices(self, course_id=None):
        if course_id:
            course = Course.objects.get(id=course_id)
            min_level = course.level_start
            max_level = course.level_end
        else:
            min_level = 1
            max_level = 8

        return [(str(i), chr(64 + i)) for i in range(min_level, max_level + 1)]

    course = forms.ModelChoiceField(queryset=Course.objects.all(), required=False, widget=forms.Select(attrs={'class': 'form-control'}), label=_('Course'))
    teacher = forms.ModelChoiceField(queryset=Teacher.objects.all(), required=False, widget=forms.Select(attrs={'class': 'form-control'}), label=_('Teacher'))
    grade = forms.ChoiceField(
        choices=[],  # Initialize empty, will set in __init__
        label=_("Max Level"),
        help_text=_("Select a level, which corresponds to a grade.")
    )
    day = forms.ChoiceField(choices=ClassSchedule.DAYS_OF_WEEK, required=False, widget=forms.Select(attrs={'class': 'form-control'}), label=_('Day of the Week'))
    start_time = forms.TimeField(required=False, widget=forms.TimeInput(attrs={'type': 'time'}), label=_('Start Time'))
    end_time = forms.TimeField(required=False, widget=forms.TimeInput(attrs={'type': 'time'}), label=_('End Time'))
    lesson_hours = forms.DecimalField(required=False, max_digits=5, decimal_places=2, label=_("Lesson Hours"), widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}))  # Changed to DecimalField
    remark = forms.CharField(required=False, widget=forms.Textarea(attrs={'placeholder': _('Remark'), 'class': 'form-control'}), label=_('Remark'))

    def __init__(self, *args, **kwargs):
        super(ClassScheduleForm, self).__init__(*args, **kwargs)
        initial_course_id = self.instance.course.id if self.instance and self.instance.course else None
        self.fields['grade'].choices = self.get_level_grade_choices(initial_course_id)

    class Meta:
        model = ClassSchedule
        fields = ['course', 'teacher', 'grade', 'day', 'start_time', 'end_time', 'lesson_hours', 'remark']


class DateInput(forms.DateInput):
    input_type = 'date'

class SessionForm(FormSettings):
    start_date = forms.DateField(required=False, widget=DateInput(attrs={'type': 'date'}), label=_('Start Date'))
    end_date = forms.DateField(required=False, widget=DateInput(attrs={'type': 'date'}), label=_('End Date'))

    def __init__(self, *args, **kwargs):
        super(SessionForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Session
        fields = ['start_date', 'end_date']
        widgets = {
            'start_date': DateInput(),
            'end_date': DateInput(),
        }

class LeaveReportTeacherForm(FormSettings):
    date = forms.DateField(widget=DateInput(attrs={'type': 'date'}), label=_('Date'))
    message = forms.CharField(widget=TextInput(), label=_('Message'))
    def __init__(self, *args, **kwargs):
        super(LeaveReportTeacherForm, self).__init__(*args, **kwargs)

    class Meta:
        model = LeaveReportTeacher
        fields = ['date', 'message']
        widgets = {
            'date': DateInput(attrs={'type': 'date'}),
        }

class SummaryTeacherForm(FormSettings):
    student = forms.ModelChoiceField(queryset=Student.objects.none(), label=_('Select Student'))
    summary = forms.Textarea()
    class Meta:
        model = SummaryTeacher
        fields = ['student', 'summary']


    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super(SummaryTeacherForm, self).__init__(*args, **kwargs)
        if teacher:
            learning_records = LearningRecord.objects.filter(teacher=teacher)
            student_ids = learning_records.values_list('student_id', flat=True).distinct()
            self.fields['student'].queryset = Student.objects.filter(id__in=student_ids)

class LeaveReportStudentForm(FormSettings):
    date = forms.DateField(widget=DateInput(attrs={'type': 'date'}), label=_('Date'))
    message = forms.CharField(widget=TextInput(), label=_('Message'))
    def __init__(self, *args, **kwargs):
        super(LeaveReportStudentForm, self).__init__(*args, **kwargs)

    class Meta:
        model = LeaveReportStudent
        fields = ['date', 'message']
        widgets = {
            'date': DateInput(attrs={'type': 'date'}),
        }

class StudentEditForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(StudentEditForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Student
        fields = CustomUserForm.Meta.fields 

class TeacherEditForm(FormSettings):
    full_name = forms.CharField(required=True, label=_('Full Name'))
    email = forms.EmailField(required=True, label=_('Email'))
    gender = forms.ChoiceField(choices=[('男', _('Male')), ('女', _('Female'))], label=_('Gender'))
    password = forms.CharField(widget=forms.PasswordInput, label=_('Password'), required=False)
    profile_pic = forms.ImageField(label=_('Profile Picture'), required=False)

    def __init__(self, *args, **kwargs):
        super(TeacherEditForm, self).__init__(*args, **kwargs)
        # Reorder fields as requested
        field_order = ['full_name', 'email', 'gender', 'password', 'profile_pic']
        self.fields = {k: self.fields[k] for k in field_order}
        # Initialize the fields with existing data
        if self.instance:
            self.fields['full_name'].initial = self.instance.admin.full_name
            self.fields['email'].initial = self.instance.admin.email
            self.fields['gender'].initial = self.instance.admin.gender
          
    class Meta:
        model = Teacher
        fields = ['full_name', 'email', 'gender', 'password', 'profile_pic']

class ResultForm(FormSettings):
    course = forms.ModelChoiceField(queryset=Course.objects.all(), required=False,  widget=forms.Select(attrs={'class': 'form-control'}), label=_('Course'))
    session = forms.ModelChoiceField(queryset=Session.objects.all(), required=False, widget=forms.Select(attrs={'class': 'form-control'}), label=_('Session'))

    def __init__(self, *args, **kwargs):
        super(ResultForm, self).__init__(*args, **kwargs)

    class Meta:
        model = StudentResult
        fields = [_('course'), _('session')]

class TeacherEditAttendanceForm(FormSettings):
    classes = forms.ModelChoiceField(
        queryset=ClassSchedule.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'disabled': 'disabled'}),
        label=_('Course')
    )
    date = forms.DateField(widget=DateInput(attrs={'type': 'date'}), label=_('Date'), disabled=True)
    
    class Meta:
        model = Attendance
        fields = ['classes', 'date']
    
    def __init__(self, *args, **kwargs):
        super(TeacherEditAttendanceForm, self).__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super(TeacherEditAttendanceForm, self).save(commit=False)
        instance.classes = self.initial['classes']
        if commit:
            instance.save()
        return instance