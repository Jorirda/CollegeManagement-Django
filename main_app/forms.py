from django import forms
from django.forms.widgets import DateInput, TextInput, TimeInput
from django.utils.translation import ugettext_lazy as _
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
    remark = forms.CharField(label=_('Remark'))
    campus = forms.ModelChoiceField(queryset=Campus.objects.all(), required=False, label=_("Campus"))
    

    def __init__(self, *args, **kwargs):
        super(StudentForm, self).__init__(*args, **kwargs)
        if self.instance.pk:  # if the instance exists (editing case)
            self.fields['campus'].initial = self.instance.campus
        # Reorder fields as requested
        field_order = [_('full_name'), _('gender'), _('date_of_birth'), _('address'), _('phone_number'),_('campus'), _('reg_date'),_('status'), _('remark')]
                         
        # Set the field order
        self.fields = {k: self.fields[k] for k in field_order}

    class Meta:
        model = Student
        fields = ['full_name', 'gender', 'date_of_birth', 'reg_date', 
                   'status', 'address', 'phone_number', 'remark'] 

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
    hourly_rate = forms.DecimalField(
        required=False,
        label=_("Hourly Rate"),
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )

    level_grade = forms.ChoiceField(
        choices=LEVEL_GRADE_CHOICES,
        label=_("Max Level"),
        help_text=_("Select a level, which corresponds to a grade.")
    )
    image = forms.ImageField(label=_('Course Image'), required=False)  # Added this line
    def __init__(self, *args, **kwargs):
        super(CourseForm, self).__init__(*args, **kwargs)
        # instance = kwargs.get('instance')
        # if instance:
        #     # Generate level choices from instance range
        #     self.fields['level'].choices = [(i, str(i)) for i in range(instance.level_start, instance.level_end + 1)]

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
    date = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={'type': 'date'}), 
        label=_('Date')
    )
    student = forms.ModelChoiceField(
        queryset=Student.objects.all(), 
        required=False, 
        label=_("Name")
    )
    course = forms.ModelChoiceField(
        queryset=Course.objects.all(), 
        required=False, 
        label=_("Course")
    )
    teacher = forms.ModelChoiceField(
        queryset=Teacher.objects.none(), 
        required=False, 
        label=_("Teacher")
    )
    semester = forms.ModelChoiceField(
        queryset=Session.objects.all(), 
        required=False, 
        label=_("Semester")
    )
    day = forms.ChoiceField(
        choices=ClassSchedule.DAYS_OF_WEEK, 
        required=False, 
        widget=forms.Select(attrs={'class': 'form-control'}), 
        label=_('Day')
    )
    start_time = forms.TimeField(
        required=False, 
        label=_("Start Time"), 
        widget=forms.TimeInput(attrs={'readonly': 'readonly'})
    )
    end_time = forms.TimeField(
        required=False, 
        label=_("End Time"), 
        widget=forms.TimeInput(attrs={'readonly': 'readonly'})
    )
    lesson_hours = forms.CharField(
        required=False, 
        label=_("Lesson Hours"), 
        disabled=True
    )

    class Meta:
        model = LearningRecord
        fields = ['date', 'day', 'student', 'course', 'teacher', 'start_time', 'end_time', 'lesson_hours', 'semester']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_time'].widget.attrs['readonly'] = True
        self.fields['end_time'].widget.attrs['readonly'] = True
        self.fields['lesson_hours'].widget.attrs['readonly'] = True  
        self.fields['day'].widget.attrs['readonly'] = True

        if 'course' in self.data and 'teacher' in self.data:
            try:
                course_id = int(self.data.get('course', 0))
                teacher_id = int(self.data.get('teacher', 0))
                class_schedule_data = self.fetch_class_schedule_data(course_id, teacher_id)
                if class_schedule_data:
                    self.fields['start_time'].initial = class_schedule_data.get('start_time')
                    self.fields['end_time'].initial = class_schedule_data.get('end_time')
                    self.fields['lesson_hours'].initial = class_schedule_data.get('lesson_hours')
                    self.fields['day'].initial = class_schedule_data.get('day')
                teachers_data = self.fetch_teacher_data(course_id)
                self.filter_teachers_by_course(course_id, teachers_data)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            course_id = self.instance.course_id
            teacher_id = self.instance.teacher_id
            class_schedule_data = self.fetch_class_schedule_data(course_id, teacher_id)
            if class_schedule_data:
                self.fields['start_time'].initial = class_schedule_data.get('start_time')
                self.fields['end_time'].initial = class_schedule_data.get('end_time')
                self.fields['lesson_hours'].initial = class_schedule_data.get('lesson_hours')
                self.fields['day'].initial = class_schedule_data.get('day')
            teachers_data = self.fetch_teacher_data(course_id)
            self.filter_teachers_by_course(course_id, teachers_data)

    def fetch_class_schedule_data(self, course_id, teacher_id):
        class_schedule = ClassSchedule.objects.filter(course_id=course_id, teacher_id=teacher_id).first()
        if class_schedule:
            return {
                'start_time': class_schedule.start_time.strftime('%H:%M') if class_schedule.start_time else None,
                'end_time': class_schedule.end_time.strftime('%H:%M') if class_schedule.end_time else None,
                'lesson_hours': class_schedule.lesson_hours if class_schedule.lesson_hours is not None else None,
                'day': class_schedule.day_of_week if class_schedule.day_of_week is not None else None
            }
        return {
            'start_time': None,
            'end_time': None,
            'lesson_hours': None,
            'day': None
        }

    def fetch_teacher_data(self, course_id):
        if course_id:
            teachers = Teacher.objects.filter(classschedule__course_id=course_id).distinct()
            return [(teacher.id, teacher.admin.full_name) for teacher in teachers]
        return []

    def filter_teachers_by_course(self, course_id, teachers_data):
        if course_id:
            self.fields['teacher'].queryset = Teacher.objects.filter(classschedule__course_id=course_id).distinct()
            self.fields['teacher'].choices = teachers_data
        else:
            self.fields['teacher'].queryset = Teacher.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        course = cleaned_data.get('course')
        teacher = cleaned_data.get('teacher')
        if course and teacher:
            class_schedule_data = self.fetch_class_schedule_data(course.id, teacher.id)
            cleaned_data['lesson_hours'] = class_schedule_data.get('lesson_hours')
        return cleaned_data

class PaymentRecordForm(FormSettings):
    payee = forms.CharField(label=_('Payee'))
    remark = forms.CharField(required=True, label=_('Remark'))
    student = forms.ModelChoiceField(queryset=Student.objects.all(), required=False, label=_("Student"))
    course = forms.ModelChoiceField(queryset=Course.objects.all(), required=False, label=_("Course"))
    date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}), label=_('Date'))
    payment_method = forms.ChoiceField(choices=[
        ('WeChat', _('WeChat')), 
        ('AliPay', _('AliPay')), 
        ('Bank Card', _('Bank Card')),
        ('Other', _('Other'))
    ], label=_('Payment Method'))
    status = forms.ChoiceField(choices=[
        ('Completed', _('Completed')), 
        ('Pending', _('Pending')), 
        ('Refund', _('Refund'))
    ], label=_('Status'))
    lesson_unit_price = forms.DecimalField(widget=forms.TextInput(attrs={'placeholder': _('¥')}), label=_('Lesson Unit Price'))
    discounted_price = forms.DecimalField(widget=forms.TextInput(attrs={'placeholder': _('¥')}), label=_('Discounted Price'))
    book_costs = forms.DecimalField(widget=forms.TextInput(attrs={'placeholder': _('¥')}), label=_('Book Costs'))
    other_fee = forms.DecimalField(widget=forms.TextInput(attrs={'placeholder': _('¥')}), label=_('Other Fee'))
    amount_due = forms.DecimalField(widget=forms.TextInput(attrs={'placeholder': _('¥')}), label=_('Amount Due'))
    amount_paid = forms.DecimalField(widget=forms.TextInput(attrs={'placeholder': _('¥')}), label=_('Amount Paid'))
    lesson_hours = forms.DecimalField(required=False, decimal_places=0, max_digits=10, initial=0, label=_("Total Lesson Hours"))


    class Meta:
        model = PaymentRecord
        fields = [
            _('date'), _('student'), 'course', _('lesson_unit_price'),
            _('discounted_price'), _('book_costs'), _('other_fee'), _('amount_due'), _('amount_paid'), 
            _('payment_method'), _('status'), _('payee'), _('remark'), _('lesson_hours')
        ] # Ensures all model fields are included

class ClassScheduleForm(forms.ModelForm):
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
    day_of_week = forms.ChoiceField(choices=ClassSchedule.DAYS_OF_WEEK, required=False, widget=forms.Select(attrs={'class': 'form-control'}), label=_('Day of the Week'))
    start_time = forms.TimeField(required=False, widget=forms.TimeInput(attrs={'type': 'time'}), label=_('Start Time'))
    end_time = forms.TimeField(required=False, widget=forms.TimeInput(attrs={'type': 'time'}), label=_('End Time'))
    lesson_hours = forms.CharField(required=False, label=_("Lesson Hours"), disabled=True)
    remark = forms.CharField(required=False, widget=forms.Textarea(attrs={'placeholder': _('Remark'), 'class': 'form-control'}), label=_('Remark'))
    hourly_rate = forms.DecimalField(max_digits=6, decimal_places=2, required=False, label=_('Hourly Rate'))  # New field

    def __init__(self, *args, **kwargs):
        super(ClassScheduleForm, self).__init__(*args, **kwargs)
        initial_course_id = self.instance.course.id if self.instance and self.instance.course else None
        self.fields['grade'].choices = self.get_level_grade_choices(initial_course_id)
        if initial_course_id:
            self.fields['hourly_rate'].initial = Course.objects.get(id=initial_course_id).hourly_rate

    class Meta:
        model = ClassSchedule
        fields = ['course', 'teacher', 'grade', 'day_of_week', 'start_time', 'end_time', 'lesson_hours', 'remark', 'hourly_rate']

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