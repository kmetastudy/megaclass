# app_home/admin.py (건강 습관 관련 부분)
from django.contrib import admin
from django.utils.html import format_html
from app_home.models import (
    HealthHabitTracker, DailyReflection, 
    DailyReflectionEvaluation, TrackerEvaluation
)

@admin.register(HealthHabitTracker)
class HealthHabitTrackerAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'slide', 'completion_rate_display', 'is_submitted', 'submitted_at', 'created_at']
    list_filter = ['is_submitted', 'slide', 'created_at', 'student__school_class']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'student__student_id']
    readonly_fields = ['created_at', 'updated_at', 'completion_stats_display']
    
    def student_name(self, obj):
        return obj.student.user.get_full_name()
    student_name.short_description = '학생 이름'
    
    def completion_rate_display(self, obj):
    # completion_rate 값을 먼저 포맷팅
        rate = getattr(obj, 'completion_rate', 0)
        rate_str = f"{rate:.1f}%"  # 미리 포맷팅
        
        # format_html에는 이미 포맷된 문자열 전달
        return format_html(
            '<span style="color: {};">{}</span>',
            'green' if rate >= 80 else 'orange' if rate >= 60 else 'red',
            rate_str  # 포맷팅된 문자열 사용
        )
    completion_rate_display.short_description = '완료율'
    
    def completion_stats_display(self, obj):
        stats = obj.get_completion_stats()
        html = '<table style="width: 100%;">'
        html += '<tr><th>약속</th><th>완료일수</th><th>완료율</th></tr>'
        
        promises = {
            '1': '바른 자세로 생활하기',
            '2': '규칙적으로 가벼운 운동하기',
            '3': '바른 식습관 기르기',
            '4': '몸을 깨끗하게 하기',
            '5': '생활 주변을 깨끗하게 하기',
            '6': '마음 건강하게 관리하기'
        }
        
        for i in range(1, 7):
            promise_stat = stats['promises_stats'][i]
            promise_name = obj.promises.get(str(i), promises.get(str(i), f'약속 {i}'))
            html += f'<tr><td>{promise_name}</td><td>{promise_stat["completed_days"]}/14</td><td>{promise_stat["rate"]}%</td></tr>'
        
        html += f'<tr style="font-weight: bold;"><td>전체</td><td>{stats["total_reflections"]}/84</td><td>{stats["completion_rate"]}%</td></tr>'
        html += '</table>'
        
        return format_html(html)
    completion_stats_display.short_description = '완료 통계'


@admin.register(DailyReflection)
class DailyReflectionAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'promise_display', 'week', 'day_display', 'reflection_date', 'is_evaluated', 'score_display']
    list_filter = ['is_evaluated', 'promise_number', 'week', 'reflection_date', 'tracker__student__school_class']
    search_fields = ['tracker__student__user__first_name', 'tracker__student__user__last_name', 'reflection_text']
    date_hierarchy = 'reflection_date'
    
    def student_name(self, obj):
        return obj.tracker.student.user.get_full_name()
    student_name.short_description = '학생'
    
    def promise_display(self, obj):
        promises = {
            1: '바른 자세',
            2: '운동',
            3: '식습관',
            4: '개인위생',
            5: '환경정리',
            6: '마음건강'
        }
        return f"{obj.promise_number}. {promises.get(obj.promise_number, '')}"
    promise_display.short_description = '약속'
    
    def day_display(self, obj):
        days = ['월', '화', '수', '목', '금', '토', '일']
        return days[obj.day - 1]
    day_display.short_description = '요일'
    
    def score_display(self, obj):
        if hasattr(obj, 'evaluation'):
            stars = '⭐' * obj.evaluation.score
            emoji = obj.evaluation.get_emoji_feedback_display()
            return format_html(f'{stars} {emoji}')
        return '-'
    score_display.short_description = '평가'


@admin.register(DailyReflectionEvaluation)
class DailyReflectionEvaluationAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'promise_number', 'week_day', 'score_display', 'emoji_feedback', 'comment', 'teacher', 'evaluated_at']
    list_filter = ['score', 'emoji_feedback', 'teacher', 'evaluated_at']
    search_fields = ['reflection__tracker__student__user__first_name', 'reflection__tracker__student__user__last_name', 'comment']
    date_hierarchy = 'evaluated_at'
    
    def student_name(self, obj):
        return obj.reflection.tracker.student.user.get_full_name()
    student_name.short_description = '학생'
    
    def promise_number(self, obj):
        return f"약속 {obj.reflection.promise_number}"
    promise_number.short_description = '약속'
    
    def week_day(self, obj):
        days = ['월', '화', '수', '목', '금', '토', '일']
        return f"{obj.reflection.week}주 {days[obj.reflection.day - 1]}"
    week_day.short_description = '주차/요일'
    
    def score_display(self, obj):
        return '⭐' * obj.score
    score_display.short_description = '점수'


@admin.register(TrackerEvaluation)
class TrackerEvaluationAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'grade_display', 'total_score', 'badges_display', 'teacher', 'evaluated_at']
    list_filter = ['grade', 'teacher', 'evaluated_at', 'tracker__student__school_class']
    search_fields = ['tracker__student__user__first_name', 'tracker__student__user__last_name', 'feedback']
    date_hierarchy = 'evaluated_at'
    
    def student_name(self, obj):
        return obj.tracker.student.user.get_full_name()
    student_name.short_description = '학생'
    
    def grade_display(self, obj):
        return obj.get_grade_display()
    grade_display.short_description = '등급'
    
    def badges_display(self, obj):
        badge_emojis = {
            'perfect': '💯',
            'consistent': '📅',
            'improved': '📈',
            'creative': '🎨',
            'positive': '☀️'
        }
        badges = [badge_emojis.get(badge, badge) for badge in obj.badges]
        return ' '.join(badges) if badges else '-'
    badges_display.short_description = '뱃지'