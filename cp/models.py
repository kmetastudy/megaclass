from django.db import models
from teacher.models import ContentType,ContentTypeCategory
from django.contrib.auth.models import User
from django.utils import timezone
from accounts.models import Teacher, Class, Student


class Contents_Template(models.Model):
    """콘텐츠 모델"""
    content_category = models.ForeignKey(ContentTypeCategory, on_delete=models.CASCADE, verbose_name='콘텐츠 타입 카테고리')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, verbose_name='콘텐츠 타입')
    title = models.CharField('제목', max_length=200)
    page = models.TextField('콘텐츠 페이지', help_text='HTML 형식의 콘텐츠')
    answer = models.TextField('정답', blank=True,null=True, help_text='객관식/단답형의 경우 정답')
    meta_data = models.JSONField('메타데이터', default=dict, blank=True)
    tags = models.JSONField('태그/평가기준', default=dict, blank=True, help_text='채점이나 평가 기준')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='생성자')
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    is_active = models.BooleanField('활성화', default=True)
    is_public = models.BooleanField('공개', default=True, help_text='다른 교사들도 사용할 수 있도록 공개')  # 추가
    view_count = models.PositiveIntegerField('조회수', default=0)  # 이 줄 추가
    
    class Meta:
        verbose_name = '콘텐츠 템플릿'
        verbose_name_plural = '콘텐츠 템플릿'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.content_category.category_name}-{self.content_type.type_name} - {self.title}"
    
    def get_preview(self, length=100):
        """콘텐츠 미리보기 텍스트 반환"""
        import re
        text = re.sub('<[^<]+?>', '', self.page)
        return text[:length] + '...' if len(text) > length else text