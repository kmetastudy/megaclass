from django import template
import math

register = template.Library()

@register.filter
def format_ms(ms):
    """밀리초를 MM:SS.ss 형식의 문자열로 변환"""
    if not isinstance(ms, (int, float)):
        return ms

    try:
        total_seconds = ms / 1000
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)
        hundredths = int((ms % 1000) / 10)
        return f"{minutes:02d}:{seconds:02d}.{hundredths:02d}"
    except (ValueError, TypeError):
        return ms

@register.filter
def get_item(dictionary, key):
    """딕셔너리에서 키로 값 가져오기"""
    return dictionary.get(key)

@register.filter
def mul(value, arg):
    """곱하기 필터"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, arg):
    """나누기 필터"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def add(value, arg):
    """더하기 필터"""
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def filter_by(queryset, args):
    """QuerySet 필터링"""
    try:
        key, value = args.split(',')
        if value == 'True':
            value = True
        elif value == 'False':
            value = False
        return queryset.filter(**{key: value})
    except:
        return queryset