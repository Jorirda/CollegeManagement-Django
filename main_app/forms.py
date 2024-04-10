from django import forms
from django.forms.widgets import DateInput, TextInput

from .models import *


class FormSettings(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormSettings, self).__init__(*args, **kwargs)
        # Here make some changes such as:
        for field in self.visible_fields():
            field.field.widget.attrs['class'] = 'form-control'


class CustomUserForm(FormSettings):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    gender = forms.ChoiceField(choices=[('男', 'Male'), ('女', 'Female')])
    password = forms.CharField(widget=forms.PasswordInput)
    widget = {
        'password': forms.PasswordInput(),
    }
    profile_pic = forms.ImageField() 
    address = forms.CharField(widget=forms.Textarea)
    
    
    contact_num = forms.CharField(required=True) #student & teachers
    remark = forms.CharField(required=True) #student & teachers

    def __init__(self, *args, **kwargs):
        super(CustomUserForm, self).__init__(*args, **kwargs)

        if kwargs.get('instance'):
            instance = kwargs.get('instance').admin.__dict__
            self.fields['password'].required = False
            for field in CustomUserForm.Meta.fields:
                self.fields[field].initial = instance.get(field)
            if self.instance.pk is not None:
                self.fields['password'].widget.attrs['placeholder'] = "Fill this only if you wish to update password"

    def clean_email(self, *args, **kwargs):
        formEmail = self.cleaned_data['email'].lower()
        if self.instance.pk is None:  # Insert
            if CustomUser.objects.filter(email=formEmail).exists():
                raise forms.ValidationError(
                    "The given email is already registered")
        else:  # Update
            dbEmail = self.Meta.model.objects.get(
                id=self.instance.pk).admin.email.lower()
            if dbEmail != formEmail:  # There has been changes
                if CustomUser.objects.filter(email=formEmail).exists():
                    raise forms.ValidationError("The given email is already registered")

        return formEmail

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'gender',  'password','profile_pic', 'address','contact_num','remark' ]


class StudentForm(CustomUserForm):
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    reg_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    state = forms.ChoiceField(choices=[('Currently Learning','Currently Learning'), ('Completed','Completed'), ('Refund', 'Refund')])
    
    def __init__(self, *args, **kwargs):
        super(StudentForm, self).__init__(*args, **kwargs)
        self.fields['remark'] = self.fields.pop('remark')
        
    class Meta(CustomUserForm.Meta):
        model = Student
        fields = CustomUserForm.Meta.fields + \
            ['course', 'session','date_of_birth','reg_date','state']


class AdminForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(AdminForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Admin
        fields = CustomUserForm.Meta.fields


class TeacherForm(CustomUserForm):
    work_type = forms.ChoiceField(choices=[('Special Teacher','Special Teacher'), ('Temporary Contract','Temporary Contract')])
    
    def __init__(self, *args, **kwargs):
        super(TeacherForm, self).__init__(*args, **kwargs)
        self.fields['remark'] = self.fields.pop('remark')
        
    class Meta(CustomUserForm.Meta):
        model = Teacher
        fields =  CustomUserForm.Meta.fields + ['course','work_type']


class CourseForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(CourseForm, self).__init__(*args, **kwargs)

    class Meta:
        fields = ['name']
        model = Course


class SubjectForm(FormSettings):

    def __init__(self, *args, **kwargs):
        super(SubjectForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Subject
        fields = ['name', 'teacher', 'course']
        

    
class PaymentRecordForm(FormSettings):
    date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    payment_method = forms.ChoiceField(choices=[('WeChat','WeChat'), ('AliPay','AliPay'), ('Bank Card', 'Bank Card'),('Other', 'Other')])
    status = forms.ChoiceField(choices=[('Completed','Completed'), ('Pending','Pending'), ('Refund', 'Refund')])
    lesson_unit_price = forms.DecimalField(widget=forms.TextInput(attrs={'placeholder': '¥'}))
    discounted_price = forms.DecimalField(widget=forms.TextInput(attrs={'placeholder': '¥'}))
    book_costs = forms.DecimalField(widget=forms.TextInput(attrs={'placeholder': '¥'}))
    other_fee = forms.DecimalField(widget=forms.TextInput(attrs={'placeholder': '¥'}))
    amount_due = forms.DecimalField(widget=forms.TextInput(attrs={'placeholder': '¥'}))
    amount_paid = forms.DecimalField(widget=forms.TextInput(attrs={'placeholder': '¥'}))
    
    
    def __init__(self, *args, **kwargs):
        super(PaymentRecordForm, self).__init__(*args, **kwargs)
     
    class Meta:
        model = PaymentRecord
        fields = ['date','student','course','lesson_unit_price','class_name','discounted_price',
                'book_costs','other_fee','amount_due','amount_paid','payment_method','status','payee','remark']

class LearningRecordForm(FormSettings):
    date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    starting_time= forms.TimeField(required=False, widget=forms.TimeInput(attrs={'type': 'time'}))
    end_time = forms.TimeField(required=False, widget=forms.TimeInput(attrs={'type': 'time'}))
    
    def __init__(self, *args, **kwargs):
        super(LearningRecordForm, self).__init__(*args, **kwargs)

    class Meta:
        model = LearningRecord
        fields = ['date','student','course','teacher','starting_time','end_time', 'class_name','remark']


class ClassScheduleForm(FormSettings):
    lesson_unit_price = forms.DecimalField(widget=forms.TextInput(attrs={'placeholder': '¥'}))
   
    def __init__(self, *args, **kwargs):
        super(ClassScheduleForm, self).__init__(*args, **kwargs)

    class Meta:
        model = ClassSchedule
        fields = ['course','lesson_unit_price','teacher','subject','class_time','remark']


class StudentQueryForm(FormSettings):
    gender = forms.ChoiceField(choices=[('Male', 'Male'), ('Female', 'Female')])
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    contact_num = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'Contact Number'}))
    state = forms.ChoiceField(choices=[('Currently Learning', 'Currently Learning'), ('Completed', 'Completed'), ('Refund', 'Refund')])
    payment_status = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Payment Status'}))
    refund_situation = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Refund Situation'}))
    reg_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    num_classes = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Number of Classes'}))
    registered_courses = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Already Registered for Courses'}))
    completed_hours = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Course Hours Completed'}))
    paid_hours = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Paid Class Hours'}))
    remaining_hours = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Remaining Class Hours'}))
    course = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Course'}))
    session = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Session'}))

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
    def __init__(self, *args, **kwargs):
        super(LeaveReportTeacherForm, self).__init__(*args, **kwargs)

    class Meta:
        model = LeaveReportTeacher
        fields = ['date', 'message']
        widgets = {
            'date': DateInput(attrs={'type': 'date'}),
        }


class FeedbackTeacherForm(FormSettings):

    def __init__(self, *args, **kwargs):
        super(FeedbackTeacherForm, self).__init__(*args, **kwargs)

    class Meta:
        model = FeedbackTeacher
        fields = ['feedback']


class LeaveReportStudentForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(LeaveReportStudentForm, self).__init__(*args, **kwargs)

    class Meta:
        model = LeaveReportStudent
        fields = ['date', 'message']
        widgets = {
            'date': DateInput(attrs={'type': 'date'}),
        }


class FeedbackStudentForm(FormSettings):

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

    class Meta(CustomUserForm.Meta):
        model = Teacher
        fields = CustomUserForm.Meta.fields


class EditResultForm(FormSettings):
    session_list = Session.objects.all()
    session_year = forms.ModelChoiceField(
        label="Session Year", queryset=session_list, required=True)

    def __init__(self, *args, **kwargs):
        super(EditResultForm, self).__init__(*args, **kwargs)

    class Meta:
        model = StudentResult
        fields = ['session_year', 'subject', 'student', 'test', 'exam']
