from django import forms
from django.contrib.auth.models import User
from .models import (
    Course, Chapter, SubChapter, Chasi, ChasiSlide, 
    CourseAssignment, ContentType, Contents, ContentsAttached
)
from accounts.models import Teacher, Class, Student

class CourseForm(forms.ModelForm):
    """코스 생성/수정 폼"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 모든 필드에 autocomplete off 추가
        for field in self.fields.values():
            field.widget.attrs['autocomplete'] = 'off'
    class Meta:
        model = Course
        fields = ['subject_name', 'target', 'description']
        widgets = {
            'subject_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '예: 수학, 영어, 과학 등'
            }),
            'target': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '예: 중학교 1학년, 고등학교 2학년 등'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '코스에 대한 설명을 입력하세요'
            }),
        }
        labels = {
            'subject_name': '과목명',
            'target': '대상',
            'description': '설명',
        }

class ChapterForm(forms.ModelForm):
    """대단원 생성/수정 폼"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 모든 필드에 autocomplete off 추가
        for field in self.fields.values():
            field.widget.attrs['autocomplete'] = 'off'
    
    class Meta:
        model = Chapter
        fields = ['chapter_title', 'chapter_order', 'description']
        widgets = {
            'chapter_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '대단원명을 입력하세요'
            }),
            'chapter_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '대단원에 대한 설명을 입력하세요'
            }),
        }
        labels = {
            'chapter_title': '대단원명',
            'chapter_order': '순서',
            'description': '설명',
        }

class SubChapterForm(forms.ModelForm):
    """소단원 생성/수정 폼"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 모든 필드에 autocomplete off 추가
        for field in self.fields.values():
            field.widget.attrs['autocomplete'] = 'off'
    class Meta:
        model = SubChapter
        fields = ['sub_chapter_title', 'sub_chapter_order', 'description']
        widgets = {
            'sub_chapter_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '소단원명을 입력하세요'
            }),
            'sub_chapter_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '소단원에 대한 설명을 입력하세요'
            }),
        }
        labels = {
            'sub_chapter_title': '소단원명',
            'sub_chapter_order': '순서',
            'description': '설명',
        }

class ChasiForm(forms.ModelForm):
    """차시 생성/수정 폼"""
  
    class Meta:
        model = Chasi
        fields = ['chasi_title', 'chasi_order', 'description', 'learning_objectives', 'duration_minutes']
        widgets = {
            'chasi_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '차시명을 입력하세요'
            }),
            'chasi_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '차시에 대한 설명을 입력하세요'
            }),
            'learning_objectives': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '학습목표를 입력하세요'
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'value': 45
            }),
        }
        labels = {
            'chasi_title': '차시명',
            'chasi_order': '순서',
            'description': '설명',
            'learning_objectives': '학습목표',
            'duration_minutes': '수업시간(분)',
        }

class ChasiSlideForm(forms.ModelForm):
    """차시 슬라이드 생성/수정 폼"""
    
    class Meta:
        model = ChasiSlide
        fields = ['slide_title', 'content', 'instructor_notes', 'estimated_time']
        widgets = {
            'slide_title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': '슬라이드 제목 (선택사항)'
            }),
            'content': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500'
            }),
            'instructor_notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'rows': 3,
                'placeholder': '강사를 위한 메모 (선택사항)'
            }),
            'estimated_time': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'min': 1,
                'max': 60
            })
        }


# class CourseAssignmentForm(forms.ModelForm):
#     """코스 할당 폼"""
    
#     class Meta:
#         model = CourseAssignment
#         fields = ['course', 'assigned_class', 'assigned_student', 'due_date']
#         widgets = {
#             'course': forms.Select(attrs={
#                 'class': 'form-control'
#             }),
#             'assigned_class': forms.Select(attrs={
#                 'class': 'form-control'
#             }),
#             'assigned_student': forms.Select(attrs={
#                 'class': 'form-control'
#             }),
#             'due_date': forms.DateTimeInput(attrs={
#                 'class': 'form-control',
#                 'type': 'datetime-local'
#             }),
#         }
#         labels = {
#             'course': '코스',
#             'assigned_class': '할당 학급',
#             'assigned_student': '할당 학생',
#             'due_date': '마감일',
#         }
    
#     def __init__(self, *args, **kwargs):
#         teacher = kwargs.pop('teacher', None)
#         super().__init__(*args, **kwargs)
        
#         if teacher:
#             self.fields['course'].queryset = Course.objects.filter(teacher=teacher)
#             self.fields['assigned_class'].queryset = Class.objects.filter(teacher=teacher)
#             self.fields['assigned_student'].queryset = Student.objects.filter(school_class__teacher=teacher)

class ContentTypeForm(forms.ModelForm):
    """컨텐츠 타입 폼"""
    
    class Meta:
        model = ContentType
        fields = ['type_name', 'description', 'icon', 'color']
        widgets = {
            'type_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '컨텐츠 타입명을 입력하세요'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '설명을 입력하세요'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '아이콘 클래스명 (예: fas fa-book)'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'value': '#007bff'
            }),
        }
        labels = {
            'type_name': '타입명',
            'description': '설명',
            'icon': '아이콘',
            'color': '색상',
        }

# forms.py
class ContentsForm(forms.ModelForm):
    """콘텐츠 생성/수정 폼"""
    
    # JSON 필드를 텍스트로 받기 위한 추가 필드 (선택사항)
    meta_data = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'style': 'display: none;'  # 숨김 처리
        })
    )
    
    tags = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'style': 'display: none;'  # 숨김 처리
        })
    )
    
    class Meta:
        model = Contents
        fields = ['content_type', 'title', 'page', 'answer']
        widgets = {
            'content_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '콘텐츠 제목을 입력하세요'
            }),
            'page': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10
            }),
            'answer': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '객관식/단답형의 경우 정답을 입력하세요'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 활성화된 콘텐츠 타입만 표시
        self.fields['content_type'].queryset = ContentType.objects.filter(is_active=True)
        # answer 필드는 선택사항
        self.fields['answer'].required = False

class ContentsForm_0622(forms.ModelForm):
    """콘텐츠 생성/수정 폼"""
    
    class Meta:
        model = Contents
        fields = ['content_type', 'title', 'page', 'answer', 'meta_data', 'tags']
        widgets = {
            'content_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500'
            }),
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': '콘텐츠 제목을 입력하세요'
            }),
            'page': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'rows': 10,
                'id': 'content-editor'
            }),
            'answer': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'rows': 3,
                'placeholder': '객관식/단답형의 경우 정답을 입력하세요'
            }),
            'meta_data': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'rows': 5,
                'id': 'metadata-editor'
            }),
            'tags': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'rows': 5,
                'id': 'tags-editor'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 활성화된 콘텐츠 타입만 표시
        self.fields['content_type'].queryset = ContentType.objects.filter(is_active=True)
        
        # JSON 필드들을 선택사항으로 설정
        self.fields['meta_data'].required = False
        self.fields['tags'].required = False
        self.fields['answer'].required = False
        
        # 위젯에서도 required 속성 제거
        self.fields['meta_data'].widget.attrs.pop('required', None)
        self.fields['tags'].widget.attrs.pop('required', None)
    
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     # 활성화된 콘텐츠 타입만 표시
    #     self.fields['content_type'].queryset = ContentType.objects.filter(is_active=True)
    #     self.fields['meta_data'].required = False
    #     self.fields['tags'].required = False
    #     self.fields['answer'].required = False



# 학생 생성을 위한 Form 정의
class StudentCreateForm(forms.Form):
    # ModelChoiceField는 queryset을 필요로 하지만, View에서 동적으로 지정할 것이므로 초기에는 비워둡니다.
    school_class = forms.ModelChoiceField(
        label="학급",
        queryset=Class.objects.none(),
        empty_label="-- 학급을 선택하세요 --",
        widget=forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500'})
    )
    student_id = forms.CharField(label="학번", max_length=20, widget=forms.TextInput(attrs={'placeholder': '예: 20250101'}))
    last_name = forms.CharField(label="성", max_length=150)
    first_name = forms.CharField(label="이름", max_length=150)
    birth_date = forms.DateField(label="생년월일", widget=forms.DateInput(attrs={'type': 'date'}))
    email = forms.EmailField(label="이메일 (선택)", required=False)
    password = forms.CharField(label="초기 비밀번호", widget=forms.PasswordInput, help_text="8자 이상으로 입력해주세요.")

    # 모든 필드에 공통적으로 적용될 스타일을 위해 widget attrs를 반복적으로 추가할 수 있습니다.
    def __init__(self, *args, **kwargs):
        super(StudentCreateForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.Select): # Select 위젯은 위에서 이미 클래스를 지정했으므로 제외
                field.widget.attrs.update({
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500'
                })



class StudentCreateForm_0609(forms.Form):
    # 각 필드에 label과 widget 속성을 정의
    school_class = forms.ModelChoiceField(
        label="학급",
        queryset=Class.objects.none(), # View에서 이 부분을 동적으로 필터링할 예정
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500'
        })
    )
    student_id = forms.CharField(
        label="학번",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500',
            'placeholder': '학번을 입력하세요'
        })
    )
    last_name = forms.CharField(
        label="성",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500',
            'placeholder': '성을 입력하세요'
        })
    )
    first_name = forms.CharField(
        label="이름",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500',
            'placeholder': '이름을 입력하세요'
        })
    )
    birth_date = forms.DateField(
        label="생년월일",
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500'
        })
    )
    email = forms.EmailField(
        label="이메일 (선택)",
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500',
            'placeholder': '이메일 주소를 입력하세요'
        })
    )
    password = forms.CharField(
        label="초기 비밀번호",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500',
            'placeholder': '8자 이상 입력'
        })
    )

class StudentCreateForm_0609(forms.ModelForm):
    """학생 생성 폼"""
    first_name = forms.CharField(
        label='이름',
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '이름을 입력하세요'
        })
    )
    last_name = forms.CharField(
        label='성',
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '성을 입력하세요'
        })
    )
    email = forms.EmailField(
        label='이메일',
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@email.com'
        })
    )
    password = forms.CharField(
        label='비밀번호',
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '비밀번호를 입력하세요'
        })
    )
    
    class Meta:
        model = Student
        fields = ['student_id', 'birth_date', 'school_class']
        widgets = {
            'student_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '학번을 입력하세요'
            }),
            'birth_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'school_class': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'student_id': '학번',
            'birth_date': '생년월일',
            'school_class': '학급',
        }
    
    def clean_student_id(self):
        student_id = self.cleaned_data['student_id']
        
        # 기존 학생 ID 중복 확인 (수정 시에는 자기 자신 제외)
        if self.instance.pk:
            if Student.objects.exclude(pk=self.instance.pk).filter(student_id=student_id).exists():
                raise forms.ValidationError('이미 사용 중인 학번입니다.')
        else:
            if Student.objects.filter(student_id=student_id).exists():
                raise forms.ValidationError('이미 사용 중인 학번입니다.')
        
        return student_id

class ClassCreateForm(forms.Form):
    """학급 생성 폼"""
    grade = forms.IntegerField(
        label='학년',
        min_value=1,
        max_value=12,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '학년을 입력하세요'
        })
    )
    class_number = forms.IntegerField(
        label='반',
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '반을 입력하세요'
        })
    )
    name = forms.CharField(
        label='학급명',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '예: 1학년 1반'
        })
    )

class BulkChapterCreateForm(forms.Form):
    """대단원 일괄 생성 폼"""
    chapter_data = forms.CharField(
        widget=forms.HiddenInput()
    )

class ContentSearchForm(forms.Form):
    """컨텐츠 검색 폼"""
    search = forms.CharField(
        label='검색어',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '제목이나 태그로 검색하세요'
        })
    )
    content_type = forms.ModelChoiceField(
        label='컨텐츠 타입',
        queryset=ContentType.objects.filter(is_active=True),
        required=False,
        empty_label='모든 타입',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
class PasswordResetForm(forms.Form):
    """비밀번호 초기화 폼"""
    new_password = forms.CharField(
        label='새 비밀번호',
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '새 비밀번호를 입력하세요'
        })
    )
    confirm_password = forms.CharField(
        label='비밀번호 확인',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '비밀번호를 다시 입력하세요'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password:
            if new_password != confirm_password:
                raise forms.ValidationError('비밀번호가 일치하지 않습니다.')
        
        return cleaned_data

class FileUploadForm(forms.ModelForm):
    """파일 업로드 폼"""
    
    class Meta:
        model = ContentsAttached
        fields = ['file', 'original_name']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.ppt,.pptx,.jpg,.jpeg,.png,.gif'
            }),
            'original_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '파일명을 입력하세요'
            }),
        }
        labels = {
            'file': '파일',
            'original_name': '파일명',
        }
    
    def clean_file(self):
        file = self.cleaned_data['file']
        
        # 파일 크기 제한 (10MB)
        if file.size > 10 * 1024 * 1024:
            raise forms.ValidationError('파일 크기는 10MB를 초과할 수 없습니다.')
        
        # 허용된 파일 형식 확인
        allowed_extensions = ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.jpg', '.jpeg', '.png', '.gif']
        file_extension = file.name.lower().split('.')[-1]
        
        if f'.{file_extension}' not in allowed_extensions:
            raise forms.ValidationError('허용되지 않는 파일 형식입니다.')
        
        return file