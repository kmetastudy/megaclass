# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import School

class TeacherRegistrationForm(UserCreationForm):
    """
    교사 회원가입 폼.
    - UserCreationForm: username, password1, password2 기본 제공
    - 여기에 first_name, last_name, email, school, employee_id, phone 등을 추가
    """
    first_name = forms.CharField(label="이름", required=True)
    last_name = forms.CharField(label="성", required=False)
    email = forms.EmailField(label="이메일", required=False)
    school = forms.ModelChoiceField(
        label="학교",
        queryset=School.objects.all(),
        required=True
    )
    employee_id = forms.CharField(label="사번", required=True)
    phone = forms.CharField(label="전화번호", required=False)

    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'password1', 'password2',  # UserCreationForm 기본 필드
            'school', 'employee_id', 'phone'
        ]
