# student/templatetags/student_filters.py
from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """값을 곱하는 필터"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def format_ms(value):
    """밀리초를 MM:SS.ms 형식으로 변환"""
    try:
        ms = float(value)
        minutes = int(ms // 60000)
        seconds = int((ms % 60000) // 1000)
        hundredths = int((ms % 1000) // 10)
        return f"{minutes:02d}:{seconds:02d}.{hundredths:02d}"
    except (ValueError, TypeError):
        return "00:00.00"

@register.filter
def get_item(dictionary, key):
    """딕셔너리에서 키로 값을 가져오는 필터"""
    return dictionary.get(key)

@register.filter
def percentage(value, total):
    """백분율 계산"""
    try:
        return int((float(value) / float(total)) * 100)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def div(value, arg):
    """나누기 필터"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def sub(value, arg):
    """빼기 필터"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0