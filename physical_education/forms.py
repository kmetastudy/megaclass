from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date
from .models import PAPSSession, PAPSSessionActivity, PAPSCategory, PAPSActivity


class PAPSSessionForm(forms.ModelForm):
    """PAPS 측정회차 생성/수정 폼"""
    
    class Meta:
        model = PAPSSession
        fields = ['school_year', 'session_type', 'name', 'measurement_date']
        
    def __init__(self, *args, **kwargs):
        self.teacher_id = kwargs.pop('teacher_id', None)
        super().__init__(*args, **kwargs)
        
        # 필드 설정
        self.fields['school_year'].widget.attrs.update({
            'class': 'form-control',
            'min': 2020,
            'max': 2050,
        })
        
        self.fields['session_type'].widget.attrs.update({
            'class': 'form-control'
        })
        
        self.fields['name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '예: 2024년도 정시 1차'
        })
        
        self.fields['measurement_date'].widget.attrs.update({
            'class': 'form-control',
            'type': 'date'
        })
        
        # 라벨 설정
        self.fields['school_year'].label = '학년도'
        self.fields['session_type'].label = '측정구분'
        self.fields['name'].label = '측정이름'
        self.fields['measurement_date'].label = '측정일자'
        
        # 도움말 텍스트 설정
        self.fields['school_year'].help_text = '측정 대상 학년도를 입력하세요'
        self.fields['session_type'].help_text = '정시는 학년도에 한번만, 수시는 여러 번 가능합니다'
        self.fields['name'].help_text = '측정회차를 구분할 수 있는 이름을 입력하세요'
        self.fields['measurement_date'].help_text = '해당 학년도 기간(3월~다음해 2월) 내에서 입력하세요'

    def clean_school_year(self):
        school_year = self.cleaned_data['school_year']
        current_year = timezone.now().year
        
        if school_year < current_year - 2 or school_year > current_year + 2:
            raise ValidationError('학년도는 현재 연도 기준 ±2년 이내로 입력해주세요.')
        
        return school_year

    def clean_measurement_date(self):
        measurement_date = self.cleaned_data['measurement_date']
        school_year = self.cleaned_data.get('school_year')
        
        if school_year and measurement_date:
            # 학년도 기간: 해당년도 3월 ~ 다음년도 2월
            start_date = date(school_year, 3, 1)
            end_date = date(school_year + 1, 2, 28)
            
            if measurement_date < start_date or measurement_date > end_date:
                raise ValidationError(
                    f'측정일자는 {school_year}년 3월 1일부터 {school_year + 1}년 2월 28일 사이에 입력해주세요.'
                )
        
        return measurement_date

    def clean(self):
        cleaned_data = super().clean()
        school_year = cleaned_data.get('school_year')
        session_type = cleaned_data.get('session_type')
        
        if school_year and session_type and self.teacher_id:
            # 정시 중복 체크
            if session_type == PAPSSession.REGULAR:
                existing_regular = PAPSSession.objects.filter(
                    teacher_id=self.teacher_id,
                    school_year=school_year,
                    session_type=PAPSSession.REGULAR
                )
                
                if self.instance.pk:
                    existing_regular = existing_regular.exclude(pk=self.instance.pk)
                
                if existing_regular.exists():
                    raise ValidationError('해당 학년도에 이미 정시 측정회차가 존재합니다.')
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.teacher_id:
            instance.teacher_id = self.teacher_id
        
        # 기본 이름 생성 (이름이 비어있는 경우)
        if not instance.name:
            instance.name = f"{instance.school_year}년도 {instance.get_session_type_display()}"
            
            # 수시인 경우 순번 추가
            if instance.session_type == PAPSSession.SUPPLEMENTARY:
                existing_count = PAPSSession.objects.filter(
                    teacher_id=self.teacher_id,
                    school_year=instance.school_year,
                    session_type=PAPSSession.SUPPLEMENTARY
                ).count()
                
                if self.instance.pk:
                    existing_count -= 1
                
                instance.name += f" {existing_count + 2}차"
            else:
                instance.name += " 1차"
        
        if commit:
            instance.save()
        
        return instance


class PAPSActivitySelectionForm(forms.Form):
    """PAPS 측정종목 선택 폼"""
    
    def __init__(self, *args, **kwargs):
        session = kwargs.pop('session', None)
        selected_grades = kwargs.pop('selected_grades', [])
        super().__init__(*args, **kwargs)
        
        if not session or not selected_grades:
            return
        
        # 각 체력요인별로 선택 필드 생성
        required_categories = PAPSCategory.objects.filter(
            evaluation_type=PAPSCategory.REQUIRED
        ).order_by('order')
        
        optional_categories = PAPSCategory.objects.filter(
            evaluation_type=PAPSCategory.OPTIONAL
        ).order_by('order')
        
        # 필수평가 종목 선택
        for category in required_categories:
            activities = PAPSActivity.objects.filter(category_id=category.id)
            choices = [(activity.id, activity.get_name_display()) for activity in activities]
            
            for grade in selected_grades:
                field_name = f"required_{category.name}_{grade}"
                self.fields[field_name] = forms.ChoiceField(
                    choices=[('', '선택하세요')] + choices,
                    required=True,
                    label=f"{grade}학년 {category.get_name_display()}",
                    widget=forms.Select(attrs={
                        'class': 'form-control',
                        'data-category': category.name,
                        'data-grade': grade
                    })
                )
        
        # 선택평가 종목 선택 (선택사항)
        for category in optional_categories:
            activities = PAPSActivity.objects.filter(category_id=category.id)
            choices = [(activity.id, activity.get_name_display()) for activity in activities]
            
            for grade in selected_grades:
                field_name = f"optional_{category.name}_{grade}"
                self.fields[field_name] = forms.ChoiceField(
                    choices=[('', '선택 안함')] + choices,
                    required=False,
                    label=f"{grade}학년 {category.get_name_display()}",
                    widget=forms.Select(attrs={
                        'class': 'form-control',
                        'data-category': category.name,
                        'data-grade': grade
                    })
                )

    def clean(self):
        cleaned_data = super().clean()
        
        # 필수평가에서 각 체력요인별로 하나씩 선택되었는지 확인
        required_categories = PAPSCategory.objects.filter(
            evaluation_type=PAPSCategory.REQUIRED
        )
        
        grades = set()
        for field_name in self.fields.keys():
            if field_name.startswith('required_') or field_name.startswith('optional_'):
                parts = field_name.split('_')
                if len(parts) >= 3:
                    grades.add(parts[2])
        
        for grade in grades:
            for category in required_categories:
                field_name = f"required_{category.name}_{grade}"
                if not cleaned_data.get(field_name):
                    raise ValidationError(
                        f"{grade}학년 {category.get_name_display()} 종목을 선택해주세요."
                    )
        
        return cleaned_data

    def save_selections(self, session, selected_grades):
        """선택된 종목들을 PAPSSessionActivity에 저장"""
        
        # 기존 선택 삭제
        PAPSSessionActivity.objects.filter(
            session_id=session.id,
            grade__in=selected_grades
        ).delete()
        
        # 새로운 선택 저장
        session_activities = []
        
        for field_name, activity_id in self.cleaned_data.items():
            if not activity_id:  # 선택되지 않은 경우 건너뛰기
                continue
                
            parts = field_name.split('_')
            if len(parts) < 3:
                continue
                
            evaluation_type, category_name, grade = parts[0], parts[1], int(parts[2])
            
            try:
                category = PAPSCategory.objects.get(name=category_name)
                activity = PAPSActivity.objects.get(id=activity_id)
                
                session_activity = PAPSSessionActivity(
                    session_id=session.id,
                    grade=grade,
                    category_id=category.id,
                    activity_id=activity.id
                )
                session_activities.append(session_activity)
                
            except (PAPSCategory.DoesNotExist, PAPSActivity.DoesNotExist):
                continue
        
        # 벌크 생성
        PAPSSessionActivity.objects.bulk_create(session_activities)
        
        return len(session_activities)