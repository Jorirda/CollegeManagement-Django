from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from django.contrib import messages
from .models import Classes, Teacher, Student, StudentResult
# from .forms import EditResultForm
from django.urls import reverse


class EditResultView(View):
    def get(self, request, *args, **kwargs):
        resultForm = EditResultForm()
        teacher = get_object_or_404(Teacher, admin=request.user)
        resultForm.fields['classes'].queryset = Classes.objects.filter(teacher=teacher)
        context = {
            'form': resultForm,
            'page_title': "Edit Student's Result"
        }
        return render(request, "teacher_template/edit_student_result.html", context)

    def post(self, request, *args, **kwargs):
        form = EditResultForm(request.POST)
        context = {'form': form, 'page_title': "Edit Student's Result"}
        if form.is_valid():
            try:
                student = form.cleaned_data.get('student')
                classes = form.cleaned_data.get('classes')
                test = form.cleaned_data.get('test')
                exam = form.cleaned_data.get('exam')
                # Validating
                result = StudentResult.objects.get(student=student, classes=classes)
                result.exam = exam
                result.test = test
                result.save()
                messages.success(request, "Result Updated")
                return redirect(reverse('edit_student_result'))
            except Exception as e:
                messages.warning(request, "Result Could Not Be Updated")
        else:
            messages.warning(request, "Result Could Not Be Updated")
        return render(request, "teacher_template/edit_student_result.html", context)
