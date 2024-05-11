from django import forms
from django.forms.widgets import DateInput, TextInput, TimeInput
from django.utils.translation import ugettext_lazy as _
from .models import *

class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField(label='Upload Excel File')
    is_teacher = forms.BooleanField(label='Is this data for teachers?', required=False, initial=False)

class FormSettings(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormSettings, self).__init__(*args, **kwargs)
        # Here make some changes such as:
        for field in self.visible_fields():
            field.field.widget.attrs['class'] = 'form-control'

class CustomUserForm(FormSettings):
    full_name = forms.CharField(required=True, label=_('Full Name'))
    email = forms.EmailField(required=True, label=_('Email'))
    gender = forms.ChoiceField(choices=[('male', _('Male')), ('female', _('Female'))], label=_('Gender'))
    password = forms.CharField(widget=forms.PasswordInput, label=_('Password'))
    profile_pic = forms.ImageField(label=_('Profile Picture')) 
    address = forms.CharField(widget=forms.Textarea, label=_('Address'))
    home_number = forms.CharField(required=True, label=_('Home Number'))
    cell_number = forms.CharField(required=True, label=_('Cell Number'))
    remark = forms.CharField(required=True, label=_('Remark'))

    class Meta:
        model = CustomUser
        fields = ['full_name', 'email', 'gender', 'password', 'profile_pic', 'address', 'home_number', 'cell_number', 'remark']

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
    

    def __init__(self, *args, **kwargs):
        super(StudentForm, self).__init__(*args, **kwargs)
       
        # Reorder fields as requested
        field_order = [_('full_name'), _('password'), _('gender'), _('date_of_birth'), _('address'), _('phone_number'), _('reg_date'),_('status'), _('remark')]
                         
        # Set the field order
        self.fields = {k: self.fields[k] for k in field_order}

    class Meta:
        model = Student
        fields = ['full_name', 'gender', 'date_of_birth', 'reg_date', 
                   'status', 'address', 'phone_number', 'remark'] 

class AdminForm(FormSettings):
    full_name = forms.CharField(required=True, label=_('Full Name'))
    email = forms.EmailField(required=True, label=_('Email'))
    gender = forms.ChoiceField(choices=[('male', _('Male')), ('female', _('Female'))], label=_('Gender'))
    password = forms.CharField(widget=forms.PasswordInput, label=_('Password'))
    profile_pic = forms.ImageField(label=_('Profile Picture'))

    def __init__(self, *args, **kwargs):
        super(AdminForm, self).__init__(*args, **kwargs)

        # Reorder fields as requested
        field_order = [_('full_name'), _('email'), _('gender'), _('password'), _('profile_pic')]

        # Set the field order
        self.fields = {k: self.fields[k] for k in field_order}

    class Meta:
        model = Admin
        fields = ['full_name', 'email', 'gender', 'password', 'profile_pic']

class TeacherForm(FormSettings):
    full_name = forms.CharField(required=True, label=_('Full Name'))
    gender = forms.ChoiceField(choices=[(' 男', _('Male')), ('女', _('Female'))], label=_('Gender'))
    password = forms.CharField(widget=forms.PasswordInput, label=_('Password'))
    address = forms.CharField(widget=forms.Textarea, label=_('Address'))  # Add this line
    phone_number = forms.CharField(max_length=20, required=False, label=_("Phone Number"))
    # institution = forms.ModelChoiceField(queryset=Institution.objects.all(), required=False, label=_("Institution"))
    campus = forms.ModelChoiceField(queryset=Campus.objects.all(), required=False, label=_("Campus"))
    course = forms.ModelChoiceField(queryset=Course.objects.all(), required=False, label=_("Course"))
    work_type = forms.ChoiceField(choices=[
        ('Full Time', _('Full Time')),
        ('Part Time', _('Part Time')),
    ],label=_("Contract"))
    remark = forms.CharField(required=True, label=_('Remark'))

    def __init__(self, *args, **kwargs):
        super(TeacherForm, self).__init__(*args, **kwargs)
       
        # Reorder fields as requested
        field_order = [_('full_name'), _('gender'), _('password'), 
                       _('address'), _('phone_number'), _('campus'), 
                       _('course'), _('work_type'), _('remark')]

        # Set the field order
        self.fields = {k: self.fields[k] for k in field_order}

    class Meta:
        model = Teacher
        fields = ['full_name', 'gender', 'password',  'address', 
                  'phone_number', 'campus', 'course', 'work_type', 'remark']

class CourseForm(FormSettings):
    name = forms.CharField(label=_('Course Name'))
    description = forms.CharField(label=_('Course Desciption'))
    # level = forms.ChoiceField(choices=[])
    # Combined choices where each number corresponds to a letter grade
    LEVEL_GRADE_CHOICES = [(str(i), chr(64 + i)) for i in range(1, 8)]
    level_grade = forms.ChoiceField(
        choices=LEVEL_GRADE_CHOICES,
        label="Level and Grade",
        help_text="Select a level, which corresponds to a grade."
    )
    def __init__(self, *args, **kwargs):
        super(CourseForm, self).__init__(*args, **kwargs)
        # instance = kwargs.get('instance')
        # if instance:
        #     # Generate level choices from instance range
        #     self.fields['level'].choices = [(i, str(i)) for i in range(instance.level_start, instance.level_end + 1)]

    class Meta:
        fields = [_('name'),'overview','level_grade']
        model = Course

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
    # institution = forms.ModelChoiceField(queryset=Institution.objects.all(), required=False, label=_("Institution"))
    def __init__(self, *args, **kwargs):
        super(CampusForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Campus
        fields = [_('name')]
            
class LearningRecordForm(FormSettings):
    date = forms.DateField(required=False, widget=DateInput(attrs={'type': 'date'}), label=_('Date'))
    start_time = forms.TimeField(required=False, widget=TimeInput(attrs={'type': 'time'}), label=_('Start Time'))
    end_time = forms.TimeField(required=False, widget=TimeInput(attrs={'type': 'time'}), label=_('End Time'))
    student = forms.ModelChoiceField(queryset=Student.objects.all(), required=False, label=_("Name"))
    course = forms.ModelChoiceField(queryset=Course.objects.all(), required=False, label=_("Course"))
    teacher = forms.ModelChoiceField(queryset=Teacher.objects.all(), required=False, label=_("Teacher"))
    lesson_hours = forms.CharField(required=False, label=_("Lesson Hours"), disabled=True)

    def __init__(self, *args, **kwargs):
        super(LearningRecordForm, self).__init__(*args, **kwargs)

        # Reorder fields as requested
        field_order = [_('student'), _('course'), _('teacher'), _('date'), _('start_time'), _('end_time'), _('lesson_hours')]

        # Set the field order
        self.fields = {k: self.fields[k] for k in field_order}

    class Meta:
        model = LearningRecord
        fields = [_('date'), _('start_time'), _('end_time'), _('student'), _('course'), _('teacher'), _('lesson_hours')]

class PaymentRecordForm(FormSettings):
    payee = forms.CharField(label=_('Payee'))
    remark = forms.CharField(required=True, label=_('Remark'))
    student = forms.ModelChoiceField(queryset=Student.objects.all(), required=False, label=_("Student"))
    course = forms.ModelChoiceField(queryset=Course.objects.all(), required=False, label=_("Course"))
    date = forms.DateField(required=False, widget=DateInput(attrs={'type': 'date'}), label=_('Date'))
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
    lesson_unit_price = forms.DecimalField(widget=TextInput(attrs={'placeholder': _('¥')}), label=_('Lesson Unit Price'))
    discounted_price = forms.DecimalField(widget=TextInput(attrs={'placeholder': _('¥')}), label=_('Discounted Price'))
    book_costs = forms.DecimalField(widget=TextInput(attrs={'placeholder': _('¥')}), label=_('Book Costs'))
    other_fee = forms.DecimalField(widget=TextInput(attrs={'placeholder': _('¥')}), label=_('Other Fee'))
    amount_due = forms.DecimalField(widget=TextInput(attrs={'placeholder': _('¥')}), label=_('Amount Due'))
    amount_paid = forms.DecimalField(widget=TextInput(attrs={'placeholder': _('¥')}), label=_('Amount Paid'))
    lesson_hours = forms.CharField(required=False, label=_("Lesson Hours"), disabled=True)
    
    def __init__(self, *args, **kwargs):
        super(PaymentRecordForm, self).__init__(*args, **kwargs)
     
    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get("student")
        course = cleaned_data.get("course")

        if student and course:
            # Retrieve the LearningRecord with matching student and course
            learning_record = LearningRecord.objects.filter(student=student, course=course).first()
            if learning_record:
                cleaned_data["lesson_hours"] = learning_record.lesson_hours

        return cleaned_data
    
    class Meta:
        model = PaymentRecord
        fields = [
            _('date'), _('student'), 'course', _('lesson_unit_price'),
            _('discounted_price'), _('book_costs'), _('other_fee'), _('amount_due'), _('amount_paid'), 
            _('payment_method'), _('status'), _('payee'), _('remark'), _('lesson_hours')
        ]

class ClassScheduleForm(FormSettings):
    course = forms.ModelChoiceField(queryset=Course.objects.all(), required=False, widget=forms.Select(attrs={'class': 'form-control'}), label=_('Course'))
    lesson_unit_price = forms.DecimalField(required=False, widget=forms.TextInput(attrs={'placeholder': _('Lesson Unit Price'), 'class': 'form-control'}), label=_('Lesson Unit Price'))
    teacher = forms.ModelChoiceField(queryset=Teacher.objects.all(), required=False, widget=forms.Select(attrs={'class': 'form-control'}), label=_('Teacher'))
    grade = forms.ModelChoiceField(queryset=Student.objects.all(), required=False, widget=forms.Select(attrs={'class': 'form-control'}), label=_('Grade'))
    start_time = forms.TimeField(required=False, widget=forms.TimeInput(attrs={'type': 'time'}), label=_('Start Time'))
    end_time = forms.TimeField(required=False, widget=forms.TimeInput(attrs={'type': 'time'}), label=_('End Time'))
    lesson_hours = forms.CharField(required=False, label=_("Lesson Hours"), disabled=True)
    remark = forms.CharField(required=False, widget=forms.Textarea(attrs={'placeholder': _('Remark'), 'class': 'form-control'}), label=_('Remark'))

    def __init__(self, *args, **kwargs):
        super(ClassScheduleForm, self).__init__(*args, **kwargs)

    class Meta:
        model = ClassSchedule
        fields = ['course', 'lesson_unit_price', 'teacher', 'grade', 'start_time', 'end_time', 'lesson_hours', 'remark']

class StudentQueryForm(FormSettings):
    gender = forms.ChoiceField(choices=[
        ('Male', _('Male')), 
        ('Female', _('Female'))
    ], label=_('Gender'))
    date_of_birth = forms.DateField(required=False, widget=DateInput(attrs={'type': 'date'}), label=_('Date of Birth'))
    contact_num = forms.CharField(required=True, widget=TextInput(attrs={'placeholder': _('Contact Number')}), label=_('Contact Number'))
    state = forms.ChoiceField(choices=[
        ('Currently Learning', _('Currently Learning')), 
        ('Completed', _('Completed')), 
        ('Refund', _('Refund'))
    ], label=_('State'))
    payment_status = forms.CharField(required=False, widget=TextInput(attrs={'placeholder': _('Payment Status')}), label=_('Payment Status'))
    refund_situation = forms.CharField(required=False, widget=TextInput(attrs={'placeholder': _('Refund Situation')}), label=_('Refund Situation'))
    reg_date = forms.DateField(required=False, widget=DateInput(attrs={'type': 'date'}), label=_('Registration Date'))
    num_classes = forms.CharField(required=False, widget=TextInput(attrs={'placeholder': _('Number of Classes')}), label=_('Number of Classes'))
    registered_courses = forms.CharField(required=False, widget=TextInput(attrs={'placeholder': _('Already Registered for Courses')}), label=_('Registered Courses'))
    completed_hours = forms.CharField(required=False, widget=TextInput(attrs={'placeholder': _('Course Hours Completed')}), label=_('Completed Hours'))
    paid_hours = forms.CharField(required=False, widget=TextInput(attrs={'placeholder': _('Paid Class Hours')}), label=_('Paid Hours'))
    remaining_hours = forms.CharField(required=False, widget=TextInput(attrs={'placeholder': _('Remaining Class Hours')}), label=_('Remaining Hours'))
    course = forms.CharField(required=False, widget=TextInput(attrs={'placeholder': _('Course')}), label=_('Course'))
    session = forms.CharField(required=False, widget=TextInput(attrs={'placeholder': _('Session')}), label=_('Session'))

    def __init__(self, *args, **kwargs):
        super(StudentQueryForm, self).__init__(*args, **kwargs)
        self.fields['remark'] = self.fields.pop('remark')

    class Meta(CustomUserForm.Meta):  
        model = StudentQuery
        fields = ['gender', 'date_of_birth', 'contact_num', 'state', 'payment_status', 
                                               'refund_situation', 'reg_date', 'num_classes', 'registered_courses', 'completed_hours', 
                                               'paid_hours', 'remaining_hours', 'course', 'session']

class SessionForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(SessionForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Session
        fields = '__all__'
        widgets = {
            _('start_year'): DateInput(attrs={'type': 'date'}),
            _('end_year'): DateInput(attrs={'type': 'date'}),
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

class FeedbackTeacherForm(FormSettings):
    feedback = forms.CharField(widget=TextInput(), label=_('Feedback'))
    def __init__(self, *args, **kwargs):
        super(FeedbackTeacherForm, self).__init__(*args, **kwargs)

    class Meta:
        model = FeedbackTeacher
        fields = ['feedback']

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

class FeedbackStudentForm(FormSettings):
    feedback = forms.CharField(widget=TextInput(), label=_('Feedback'))
    def __init__(self, *args, **kwargs):
        super(FeedbackStudentForm, self).__init__(*args, **kwargs)

    class Meta:
        model = FeedbackStudent
        fields = [_('feedback')]

class StudentEditForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(StudentEditForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Student
        fields = CustomUserForm.Meta.fields 

class TeacherEditForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(TeacherEditForm, self).__init__(*args, **kwargs)
        self.fields['work_type'].required = False  # Make 'work_type' field optional

    class Meta(CustomUserForm.Meta):
        model = Teacher
        fields = CustomUserForm.Meta.fields + [_('work_type')]  # Add 'work_type' to the fields list

class EditResultForm(FormSettings):
    session_list = Session.objects.all()
    session_year = forms.ModelChoiceField(
        queryset=session_list, label=_("Session Year"), required=True)

    def __init__(self, *args, **kwargs):
        super(EditResultForm, self).__init__(*args, **kwargs)

    class Meta:
        model = StudentResult
        fields = [_('session_year'), _('classes'), _('student'), _('test'), _('exam')]
