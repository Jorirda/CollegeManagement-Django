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
    first_name = forms.CharField(required=True, label=_('First Name'))
    last_name = forms.CharField(required=True, label=_('Last Name'))
    email = forms.EmailField(required=True, label=_('Email'))
    gender = forms.ChoiceField(choices=[('male', _('Male')), ('female', _('Female'))], label=_('Gender'))
    password = forms.CharField(widget=forms.PasswordInput, label=_('Password'))
    profile_pic = forms.ImageField(label=_('Profile Picture')) 
    address = forms.CharField(widget=forms.Textarea, label=_('Address'))
    contact_num = forms.CharField(required=True, label=_('Contact Number'))
    remark = forms.CharField(required=True, label=_('Remark'))

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'gender', 'password', 'profile_pic', 'address', 'contact_num', 'remark']

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
    date_of_birth = forms.DateField(required=False, label="Date of Birth", widget=forms.DateInput(attrs={'type': 'date'}))
    reg_date = forms.DateField(required=False, label="Registration Date", widget=forms.DateInput(attrs={'type': 'date'}))
    state = forms.ChoiceField(choices=[('Currently Learning', 'Currently Learning'), ('Completed', 'Completed'), ('Refund', 'Refund')], label="State")
    
    # Include new fields: campus, grade, home_number, cell_number
    campus = forms.ModelChoiceField(queryset=Campus.objects.all(), required=False)
    grade = forms.CharField(max_length=10, required=False, label="Grade")
    home_number = forms.CharField(max_length=20, required=False, label="Home Number")
    cell_number = forms.CharField(max_length=20, required=False, label="Cell Number")

    def __init__(self, *args, **kwargs):
        super(StudentForm, self).__init__(*args, **kwargs)
        self.fields['remark'] = self.fields.pop('remark')
        # Hide the contact num field
        self.fields.pop('contact_num')
        
        # Reorder fields as requested
        field_order = ['first_name', 'last_name', 'email', 'home_number', 'cell_number', 
                       'gender', 'password', 'profile_pic', 'address', 'campus', 
                       'course', 'grade', 'session', 'date_of_birth', 'reg_date', 
                       'state', 'remark']
        
        # Set the field order
        self.fields = {k: self.fields[k] for k in field_order}

    class Meta(CustomUserForm.Meta):
        model = Student
        fields = CustomUserForm.Meta.fields + \
            ['course', 'session', 'date_of_birth', 'reg_date', 'state', 'campus', 'grade', 'home_number', 'cell_number']


class AdminForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(AdminForm, self).__init__(*args, **kwargs)

        # Reorder fields as requested
        field_order = ['first_name', 'last_name', 'email', 'gender', 'password', 'profile_pic']

        # Set the field order
        self.fields = {k: self.fields[k] for k in field_order}

    class Meta(CustomUserForm.Meta):
        model = Admin
        fields = CustomUserForm.Meta.fields


class TeacherForm(CustomUserForm):
    work_type = forms.ChoiceField(choices=[('Special Teacher', 'Special Teacher'), ('Temporary Contract', 'Temporary Contract')])
    home_number = forms.CharField(max_length=20, required=False)
    cell_number = forms.CharField(max_length=20, required=False)
    campus = forms.ModelChoiceField(queryset=Campus.objects.all(), required=False)

    def __init__(self, *args, **kwargs):
        super(TeacherForm, self).__init__(*args, **kwargs)
        self.fields['remark'] = self.fields.pop('remark')
        # Hide the contact num field
        self.fields.pop('contact_num')
        
        # Reorder fields as requested
        field_order = ['first_name', 'last_name', 'email', 'home_number', 'cell_number', 
                       'gender', 'password', 'profile_pic', 'address', 
                       'work_type', 'remark', 'course', 'campus']

        # Set the field order
        self.fields = {k: self.fields[k] for k in field_order}

    class Meta(CustomUserForm.Meta):
        model = Teacher
        fields = CustomUserForm.Meta.fields + ['course', 'work_type', 'home_number', 'cell_number', 'campus']


class CourseForm(FormSettings):
    name = forms.CharField(label=_('Course Name'))
    def __init__(self, *args, **kwargs):
        super(CourseForm, self).__init__(*args, **kwargs)

    class Meta:
        fields = ['name']
        model = Course

class SubjectForm(FormSettings):
    name = forms.CharField(label=_('Subject Name'))
    teacher = forms.ModelChoiceField(queryset=Teacher.objects.all(), label=_('Teacher'))
    course = forms.ModelChoiceField(queryset=Course.objects.all(), label=_('Course'))
    def __init__(self, *args, **kwargs):
        super(SubjectForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Subject
        fields = ['name', 'teacher', 'course']

class InstitutionForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(InstitutionForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Institution
        fields = ['name']

class CampusForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(CampusForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Campus
        fields = ['name', 'institution']
            
class PaymentRecordForm(FormSettings):
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
    
    def __init__(self, *args, **kwargs):
        super(PaymentRecordForm, self).__init__(*args, **kwargs)
     
    class Meta:
        model = PaymentRecord
        fields = [
        _('date'), _('student'), _('course'), _('lesson_unit_price'), _('class_name'), 
        _('discounted_price'), _('book_costs'), _('other_fee'), _('amount_due'), _('amount_paid'), 
        _('payment_method'), _('status'), _('payee'), _('remark')
    ]

class LearningRecordForm(FormSettings):
    date = forms.DateField(required=False, widget=DateInput(attrs={'type': 'date'}), label=_('Date'))
    starting_time = forms.TimeField(required=False, widget=TimeInput(attrs={'type': 'time'}), label=_('Starting Time'))
    end_time = forms.TimeField(required=False, widget=TimeInput(attrs={'type': 'time'}), label=_('End Time'))
    
    def __init__(self, *args, **kwargs):
        super(LearningRecordForm, self).__init__(*args, **kwargs)

    class Meta:
        model = LearningRecord
        fields = [_('date'), _('student'), _('course'),_('teacher'),_('starting_time'),_('end_time'), _('class_name'),_('remark')]

class ClassScheduleForm(FormSettings):
    lesson_unit_price = forms.DecimalField(widget=TextInput(attrs={'placeholder': _('¥')}), label=_('Lesson Unit Price'))
   
    def __init__(self, *args, **kwargs):
        super(ClassScheduleForm, self).__init__(*args, **kwargs)

    class Meta:
        model = ClassSchedule
        fields = ['course','lesson_unit_price','teacher','subject','class_time','remark']

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
            'start_year': DateInput(attrs={'type': 'date'}),
            'end_year': DateInput(attrs={'type': 'date'}),
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
        fields = ['feedback']


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
        fields = CustomUserForm.Meta.fields + ['work_type']  # Add 'work_type' to the fields list


class EditResultForm(FormSettings):
    session_list = Session.objects.all()
    session_year = forms.ModelChoiceField(
        queryset=session_list, label=_("Session Year"), required=True)

    def __init__(self, *args, **kwargs):
        super(EditResultForm, self).__init__(*args, **kwargs)

    class Meta:
        model = StudentResult
        fields = ['session_year', 'subject', 'student', 'test', 'exam']
