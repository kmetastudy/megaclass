from functools import wraps
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Course, Chapter, SubChapter, Chasi, ChasiSlide

def teacher_required(view_func):
    """교사 권한 필요한 뷰 데코레이터"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # 로그인 확인은 @login_required 데코레이터가 처리하므로 여기서는 생략
        if not hasattr(request.user, 'teacher'):
            messages.error(request, '교사만 접근 가능합니다.')
            return redirect('accounts:login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def course_access_required(view_func):
    """코스 접근 권한 확인 데코레이터"""
    @wraps(view_func)
    def _wrapped_view(request, course_id, *args, **kwargs):
        try:
            # teacher__user 대신 teacher로 직접 접근
            course = Course.objects.get(id=course_id, teacher=request.user.teacher)
            request.course = course
            return view_func(request, course_id, *args, **kwargs)
        except Course.DoesNotExist:
            messages.error(request, '해당 코스에 접근할 권한이 없습니다.')
            return redirect('teacher:course_list')
        except AttributeError:
            messages.error(request, '교사만 접근 가능합니다.')
            return redirect('accounts:login')
    return _wrapped_view

def chapter_access_required(view_func):
    """대단원 접근 권한 확인 데코레이터"""
    @wraps(view_func)
    def _wrapped_view(request, chapter_id, *args, **kwargs):
        try:
            chapter = Chapter.objects.get(id=chapter_id, subject__teacher=request.user.teacher)
            request.chapter = chapter
            request.course = chapter.subject
            return view_func(request, chapter_id, *args, **kwargs)
        except Chapter.DoesNotExist:
            messages.error(request, '해당 대단원에 접근할 권한이 없습니다.')
            return redirect('teacher:course_list')
        except AttributeError:
            messages.error(request, '교사만 접근 가능합니다.')
            return redirect('accounts:login')
    return _wrapped_view

def subchapter_access_required(view_func):
    """소단원 접근 권한 확인 데코레이터"""
    @wraps(view_func)
    def _wrapped_view(request, subchapter_id, *args, **kwargs):
        try:
            subchapter = SubChapter.objects.get(id=subchapter_id, subject__teacher=request.user.teacher)
            request.subchapter = subchapter
            request.chapter = subchapter.chapter
            request.course = subchapter.subject
            return view_func(request, subchapter_id, *args, **kwargs)
        except SubChapter.DoesNotExist:
            messages.error(request, '해당 소단원에 접근할 권한이 없습니다.')
            return redirect('teacher:course_list')
        except AttributeError:
            messages.error(request, '교사만 접근 가능합니다.')
            return redirect('accounts:login')
    return _wrapped_view

def chasi_access_required(view_func):
    """차시 접근 권한 확인 데코레이터"""
    @wraps(view_func)
    def _wrapped_view(request, chasi_id, *args, **kwargs):
        try:
            chasi = Chasi.objects.get(id=chasi_id, subject__teacher=request.user.teacher)
            request.chasi = chasi
            request.subchapter = chasi.sub_chapter
            request.chapter = chasi.chapter
            request.course = chasi.subject
            return view_func(request, chasi_id, *args, **kwargs)
        except Chasi.DoesNotExist:
            messages.error(request, '해당 차시에 접근할 권한이 없습니다.')
            return redirect('teacher:course_list')
        except AttributeError:
            messages.error(request, '교사만 접근 가능합니다.')
            return redirect('accounts:login')
    return _wrapped_view

def slide_access_required(view_func):
    """슬라이드 접근 권한 확인 데코레이터"""
    @wraps(view_func)
    def _wrapped_view(request, slide_id, *args, **kwargs):
        try:
            slide = ChasiSlide.objects.get(id=slide_id, chasi__subject__teacher=request.user.teacher)
            request.slide = slide
            request.chasi = slide.chasi
            request.subchapter = slide.chasi.sub_chapter
            request.chapter = slide.chasi.chapter
            request.course = slide.chasi.subject
            return view_func(request, slide_id, *args, **kwargs)
        except ChasiSlide.DoesNotExist:
            messages.error(request, '해당 슬라이드에 접근할 권한이 없습니다.')
            return redirect('teacher:course_list')
        except AttributeError:
            messages.error(request, '교사만 접근 가능합니다.')
            return redirect('accounts:login')
    return _wrapped_view

def ajax_teacher_required(view_func):
    """AJAX 요청용 교사 권한 확인 데코레이터"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'error': '로그인이 필요합니다.'}, status=401)
        
        if not hasattr(request.user, 'teacher'):
            return JsonResponse({'success': False, 'error': '교사만 접근 가능합니다.'}, status=403)
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def superuser_required(view_func):
    """슈퍼유저 권한 필요한 뷰 데코레이터"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, '로그인이 필요합니다.')
            return redirect('accounts:login')
        
        if not request.user.is_superuser:
            messages.error(request, '관리자만 접근 가능합니다.')
            return redirect('teacher:dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def permission_required_with_message(permission, message=None):
    """권한 확인과 함께 사용자 정의 메시지를 출력하는 데코레이터"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, '로그인이 필요합니다.')
                return redirect('accounts:login')
            
            if not request.user.has_perm(permission):
                error_message = message or f'{permission} 권한이 필요합니다.'
                messages.error(request, error_message)
                return redirect('teacher:dashboard')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def validate_teacher_ownership(model_class, id_param='id', redirect_url='teacher:dashboard'):
    """교사 소유권 확인 데코레이터 팩토리"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            try:
                object_id = kwargs.get(id_param)
                if not object_id:
                    messages.error(request, '잘못된 요청입니다.')
                    return redirect(redirect_url)
                
                # 모델에 따른 소유권 확인 로직
                if model_class == Course:
                    obj = get_object_or_404(model_class, id=object_id, teacher=request.user.teacher)
                elif model_class == Chapter:
                    obj = get_object_or_404(model_class, id=object_id, subject__teacher=request.user.teacher)
                elif model_class == SubChapter:
                    obj = get_object_or_404(model_class, id=object_id, subject__teacher=request.user.teacher)
                elif model_class == Chasi:
                    obj = get_object_or_404(model_class, id=object_id, subject__teacher=request.user.teacher)
                elif model_class == ChasiSlide:
                    obj = get_object_or_404(model_class, id=object_id, chasi__subject__teacher=request.user.teacher)
                else:
                    messages.error(request, '지원하지 않는 모델입니다.')
                    return redirect(redirect_url)
                
                # 객체를 request에 추가
                setattr(request, model_class.__name__.lower(), obj)
                
                return view_func(request, *args, **kwargs)
                
            except Exception as e:
                messages.error(request, f'접근 권한이 없습니다: {str(e)}')
                return redirect(redirect_url)
                
        return _wrapped_view
    return decorator

def class_access_required(view_func):
    """학급 접근 권한 확인 데코레이터"""
    @wraps(view_func)
    def _wrapped_view(request, class_id, *args, **kwargs):
        from accounts.models import Class
        try:
            school_class = Class.objects.get(id=class_id, teacher=request.user.teacher)
            request.school_class = school_class
            return view_func(request, class_id, *args, **kwargs)
        except Class.DoesNotExist:
            messages.error(request, '해당 학급에 접근할 권한이 없습니다.')
            return redirect('teacher:class_list')
        except AttributeError:
            messages.error(request, '교사만 접근 가능합니다.')
            return redirect('accounts:login')
    return _wrapped_view

def student_access_required(view_func):
    """학생 접근 권한 확인 데코레이터"""
    @wraps(view_func)
    def _wrapped_view(request, student_id, *args, **kwargs):
        from accounts.models import Student
        try:
            student = Student.objects.get(id=student_id, school_class__teachers=request.user.teacher)
            request.student = student
            return view_func(request, student_id, *args, **kwargs)
        except Student.DoesNotExist:
            messages.error(request, '해당 학생에 접근할 권한이 없습니다.')
            return redirect('teacher:student_list')
        except AttributeError:
            messages.error(request, '교사만 접근 가능합니다.')
            return redirect('accounts:login')
    return _wrapped_view

def ajax_course_access_required(view_func):
    """AJAX용 코스 접근 권한 확인 데코레이터"""
    @wraps(view_func)
    def _wrapped_view(request, course_id, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'error': '로그인이 필요합니다.'}, status=401)
        
        if not hasattr(request.user, 'teacher'):
            return JsonResponse({'success': False, 'error': '교사만 접근 가능합니다.'}, status=403)
        
        try:
            course = Course.objects.get(id=course_id, teacher=request.user.teacher)
            request.course = course
            return view_func(request, course_id, *args, **kwargs)
        except Course.DoesNotExist:
            return JsonResponse({'success': False, 'error': '해당 코스에 접근할 권한이 없습니다.'}, status=404)
    return _wrapped_view

def ajax_chasi_access_required(view_func):
    """AJAX용 차시 접근 권한 확인 데코레이터"""
    @wraps(view_func)
    def _wrapped_view(request, chasi_id, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'error': '로그인이 필요합니다.'}, status=401)
        
        if not hasattr(request.user, 'teacher'):
            return JsonResponse({'success': False, 'error': '교사만 접근 가능합니다.'}, status=403)
        
        try:
            chasi = Chasi.objects.get(id=chasi_id, subject__teacher=request.user.teacher)
            request.chasi = chasi
            return view_func(request, chasi_id, *args, **kwargs)
        except Chasi.DoesNotExist:
            return JsonResponse({'success': False, 'error': '해당 차시에 접근할 권한이 없습니다.'}, status=404)
    return _wrapped_view