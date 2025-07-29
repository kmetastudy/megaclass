# super_agent/models.py
# 기존 teacher/models.py의 모델들을 super_agent로 이동하거나 import

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from accounts.models import Teacher, Class, Student
import uuid
from datetime import datetime

# teacher.models의 모델들을 참조하거나 이곳으로 이동
# 현재는 teacher.models를 그대로 사용하고 추가 모델만 여기에 정의


class AIGenerationLog(models.Model):
    """AI 생성 로그 모델"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="사용자")
    prompt = models.TextField("프롬프트")
    ai_provider = models.CharField(
        "AI 프로바이더",
        max_length=20,
        choices=[
            ("claude", "Claude"),
            ("gemini", "Gemini"),
            ("chatgpt", "ChatGPT"),
            ("grok", "Grok"),
        ],
    )
    content_type = models.CharField("콘텐츠 타입", max_length=50)
    generated_content_id = models.IntegerField(
        "생성된 콘텐츠 ID", null=True, blank=True
    )
    success = models.BooleanField("성공 여부", default=True)
    error_message = models.TextField("오류 메시지", blank=True)
    processing_time = models.FloatField("처리 시간(초)", null=True, blank=True)
    created_at = models.DateTimeField("생성일", auto_now_add=True)

    class Meta:
        verbose_name = "AI 생성 로그"
        verbose_name_plural = "AI 생성 로그"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.ai_provider} - {self.content_type} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"


class AgentSession(models.Model):
    """에이전트 세션 관리"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="사용자")
    session_id = models.CharField("세션 ID", max_length=100, unique=True)
    current_course_id = models.IntegerField("현재 코스 ID", null=True, blank=True)
    current_content_id = models.IntegerField("현재 콘텐츠 ID", null=True, blank=True)
    workspace_state = models.JSONField("워크스페이스 상태", default=dict)
    last_activity = models.DateTimeField("마지막 활동", auto_now=True)
    created_at = models.DateTimeField("생성일", auto_now_add=True)

    class Meta:
        verbose_name = "에이전트 세션"
        verbose_name_plural = "에이전트 세션"

    def __str__(self):
        return f"{self.user.username} - {self.session_id}"
