from django.shortcuts import render, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Count, Avg, Q
from django.core.paginator import Paginator
from .models import *
import json
from datetime import datetime

# 메인 페이지
def index(request):
    """메인 페이지"""
    return render(request, 'index.html')

# 유틸리티 함수들
def get_user_type(user):
    """사용자 타입 확인"""
    if hasattr(user, 'teacher'):
        return 'teacher', user.teacher
    elif hasattr(user, 'student'):
        return 'student', user.student
    return None, None

def paginate_data(queryset, page_number, page_size=20):
    """페이지네이션"""
    paginator = Paginator(queryset, page_size)
    page = paginator.get_page(page_number)
    return {
        'results': [item.to_dict() if hasattr(item, 'to_dict') else item for item in page.object_list],
        'count': paginator.count,
        'page': page.number,
        'total_pages': paginator.num_pages,
        'has_next': page.has_next(),
        'has_previous': page.has_previous()
    }

# === 인증 관련 API ===

@csrf_exempt
@require_http_methods(["POST"])
def user_login(request):
    """사용자 로그인"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            user_data = {
                'id': user.id,
                'username': user.username,
                'name': user.get_full_name(),
                'email': user.email,
            }
            
            if hasattr(user, 'teacher'):
                user_data['type'] = 'teacher'
                user_data['profile'] = user.teacher.to_dict()
            elif hasattr(user, 'student'):
                user_data['type'] = 'student'
                user_data['profile'] = user.student.to_dict()
            
            return JsonResponse({
                'success': True,
                'user': user_data
            })
        else:
            return JsonResponse({'error': '잘못된 사용자명 또는 비밀번호입니다.'}, status=400)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@require_http_methods(["POST"])
def user_logout(request):
    """사용자 로그아웃"""
    logout(request)
    return JsonResponse({'success': True})

@require_http_methods(["GET"])
def user_profile(request):
    """사용자 프로필 조회"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    user_data = {
        'id': request.user.id,
        'username': request.user.username,
        'name': request.user.get_full_name(),
        'email': request.user.email,
    }
    
    if hasattr(request.user, 'teacher'):
        user_data['type'] = 'teacher'
        user_data['profile'] = request.user.teacher.to_dict()
    elif hasattr(request.user, 'student'):
        user_data['type'] = 'student'
        user_data['profile'] = request.user.student.to_dict()
    
    return JsonResponse({'user': user_data})

# === 학급 관리 API ===

@require_http_methods(["GET"])
def class_list(request):
    """학급 목록 조회"""
    if not hasattr(request.user, 'teacher'):
        return JsonResponse({'error': '교사만 접근 가능합니다.'}, status=403)
    
    classes = Class.objects.filter(teacher=request.user.teacher)
    page = request.GET.get('page', 1)
    result = paginate_data(classes, page)
    
    return JsonResponse(result)

@csrf_exempt
@require_http_methods(["POST"])
def class_create(request):
    """학급 생성"""
    if not hasattr(request.user, 'teacher'):
        return JsonResponse({'error': '교사만 접근 가능합니다.'}, status=403)
    
    try:
        data = json.loads(request.body)
        
        school_class = Class.objects.create(
            school=request.user.teacher.school,
            teacher=request.user.teacher,
            grade=data['grade'],
            class_number=data['class_number'],
            name=data['name']
        )
        
        return JsonResponse({
            'success': True,
            'class': school_class.to_dict()
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@require_http_methods(["GET"])
def student_list(request):
    """학생 목록 조회"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    user_type, user_obj = get_user_type(request.user)
    
    if user_type == 'teacher':
        class_id = request.GET.get('class_id')
        if class_id:
            students = Student.objects.filter(school_class_id=class_id, school_class__teacher=user_obj)
        else:
            students = Student.objects.filter(school_class__teacher=user_obj)
    elif user_type == 'student':
        students = Student.objects.filter(school_class=user_obj.school_class)
    else:
        return JsonResponse({'error': 'Invalid user type'}, status=403)
    
    page = request.GET.get('page', 1)
    result = paginate_data(students, page)
    
    return JsonResponse(result)

@csrf_exempt
@require_http_methods(["POST"])
def student_create(request):
    """학생 등록"""
    if not hasattr(request.user, 'teacher'):
        return JsonResponse({'error': '교사만 접근 가능합니다.'}, status=403)
    
    try:
        data = json.loads(request.body)
        
        # 사용자 계정 생성
        user = User.objects.create_user(
            username=data['username'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data.get('email', '')
        )
        
        # 학생 정보 생성
        class_obj = Class.objects.get(id=data['class_id'], teacher=request.user.teacher)
        student = Student.objects.create(
            user=user,
            school_class=class_obj,
            student_id=data['student_id'],
            birth_date=data['birth_date']
        )
        
        return JsonResponse({
            'success': True,
            'student': student.to_dict()
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# === 코스 관리 API ===

@require_http_methods(["GET"])
def course_list(request):
    """코스 목록 조회"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    user_type, user_obj = get_user_type(request.user)
    
    if user_type == 'teacher':
        courses = Course.objects.filter(teacher=user_obj)
    elif user_type == 'student':
        # 학생에게 할당된 코스들
        assigned_courses = CourseAssignment.objects.filter(
            Q(assigned_class=user_obj.school_class) | Q(assigned_student=user_obj)
        ).values_list('course_id', flat=True)
        courses = Course.objects.filter(id__in=assigned_courses)
    else:
        return JsonResponse({'error': 'Invalid user type'}, status=403)
    
    page = request.GET.get('page', 1)
    result = paginate_data(courses, page)
    
    return JsonResponse(result)

@csrf_exempt
@require_http_methods(["POST"])
def course_create(request):
    """코스 생성"""
    if not hasattr(request.user, 'teacher'):
        return JsonResponse({'error': '교사만 접근 가능합니다.'}, status=403)
    
    try:
        data = json.loads(request.body)
        
        course = Course.objects.create(
            subject_name=data['subject_name'],
            target=data['target'],
            description=data.get('description', ''),
            teacher=request.user.teacher
        )
        
        return JsonResponse({
            'success': True,
            'course': course.to_dict()
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@require_http_methods(["GET"])
def content_type_list(request):
    """컨텐츠 타입 목록"""
    content_types = ContentType.objects.all()
    return JsonResponse({
        'content_types': [ct.to_dict() for ct in content_types]
    })

@require_http_methods(["GET"])
def dashboard_stats(request):
    """대시보드 통계 데이터"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    user_type, user_obj = get_user_type(request.user)
    stats = {}
    
    if user_type == 'teacher':
        # 교사 통계
        courses = Course.objects.filter(teacher=user_obj)
        students = Student.objects.filter(school_class__teacher=user_obj)
        
        stats = {
            'total_courses': courses.count(),
            'total_students': students.count(),
            'total_classes': Class.objects.filter(teacher=user_obj).count(),
            'recent_submissions': StudentAnswer.objects.filter(
                slide__chasi__subject__teacher=user_obj
            ).count()
        }
    
    elif user_type == 'student':
        # 학생 통계
        assigned_courses = CourseAssignment.objects.filter(
            Q(assigned_class=user_obj.school_class) | Q(assigned_student=user_obj)
        )
        
        my_progress = StudentProgress.objects.filter(student=user_obj)
        
        stats = {
            'assigned_courses': assigned_courses.count(),
            'completed_slides': my_progress.filter(is_completed=True).count(),
            'total_slides': my_progress.count(),
            'submitted_answers': StudentAnswer.objects.filter(student=user_obj).count()
        }
    
    return JsonResponse(stats)