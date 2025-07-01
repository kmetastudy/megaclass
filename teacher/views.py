from django.shortcuts import render, redirect, get_object_or_404
import io
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.db import transaction
from django.db import models
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
import json
from django.db.models import Count, Sum, Avg, Max, Min, Q
import csv
from django.utils.safestring import mark_safe # mark_safe 추가

# 모델 import - 코스 관련 제거
from .models import Course, CourseAssignment,Contents
from accounts.models import Teacher, Class, Student,ClassTeacher
from .forms import StudentCreateForm, ClassCreateForm
from .decorators import teacher_required
from .utils import get_teacher_dashboard_stats

from .contents_views import *
from .chasi_views import *
from .api_views import *
from .courses import *
# ========================================
# 대시보드 뷰
# ========================================

# teacher/views.py의 dashboard_view 함수를 다음으로 교체하세요:

@login_required
@teacher_required
def dashboard_view(request):
    """개선된 교사 대시보드"""
    teacher = request.user.teacher
    from datetime import timedelta
    from django.utils import timezone
    from student.models import StudentAnswer
    
    # 기본 통계 데이터
    stats = get_teacher_dashboard_stats(teacher)
    
    # 현재 시간 기준
    now = timezone.now()
    one_week_ago = now - timedelta(days=7)
    one_month_ago = now - timedelta(days=30)
    
    # 제출 답안 통계 (누적, 월간, 주간)
    try:
        all_submissions = StudentAnswer.objects.filter(
            slide__chasi__subject__teacher=teacher
        )
        
        stats['total_submissions'] = all_submissions.count()
        stats['monthly_submissions'] = all_submissions.filter(
            submitted_at__gte=one_month_ago
        ).count()
        stats['weekly_submissions'] = all_submissions.filter(
            submitted_at__gte=one_week_ago
        ).count()
        
        # 정답률, 오답률, 미제출률 계산
        total_assigned_problems = ChasiSlide.objects.filter(
            chasi__subject__assignments__isnull=False,
            chasi__subject__teacher=teacher
        ).count() * Student.objects.filter(
            school_class__teachers=teacher
        ).count()
        
        if total_assigned_problems > 0:
            correct_count = all_submissions.filter(is_correct=True).count()
            wrong_count = all_submissions.filter(is_correct=False).count()
            submitted_count = all_submissions.count()
            
            stats['correct_rate'] = round((correct_count / total_assigned_problems * 100), 1)
            stats['wrong_rate'] = round((wrong_count / total_assigned_problems * 100), 1)
            stats['no_submit_rate'] = round(((total_assigned_problems - submitted_count) / total_assigned_problems * 100), 1)
        else:
            stats['correct_rate'] = 0
            stats['wrong_rate'] = 0
            stats['no_submit_rate'] = 100
        
        # 40점 미만 비율 (취약점 비율)
        total_evaluations = all_submissions.filter(score__isnull=False).count()
        weak_evaluations = all_submissions.filter(score__lt=40).count()
        stats['weakness_rate'] = round((weak_evaluations / total_evaluations * 100), 1) if total_evaluations > 0 else 0
        
    except:
        # StudentAnswer 모델이 없는 경우 기본값
        stats.update({
            'total_submissions': 0,
            'monthly_submissions': 0,
            'weekly_submissions': 0,
            'correct_rate': 0,
            'wrong_rate': 0,
            'no_submit_rate': 100,
            'weakness_rate': 0
        })
    
    # 전체 반의 평균 성취도
    classes_with_stats = Class.objects.filter(teachers=teacher).annotate(
        student_count=Count('student')
    )
    
    total_achievement = 0
    class_count = 0
    
    for class_obj in classes_with_stats:
        try:
            class_submissions = StudentAnswer.objects.filter(
                student__school_class=class_obj
            )
            if class_submissions.exists():
                class_correct = class_submissions.filter(is_correct=True).count()
                class_total = class_submissions.count()
                class_achievement = (class_correct / class_total * 100) if class_total > 0 else 0
                total_achievement += class_achievement
                class_count += 1
        except:
            pass
    
    stats['avg_class_achievement'] = round(total_achievement / class_count, 1) if class_count > 0 else 0
    
    # 전체 코스별 평균 진도율
    courses = Course.objects.filter(teacher=teacher)
    total_progress = 0
    course_count = 0
    
    for course in courses:
        total_slides = ChasiSlide.objects.filter(chasi__subject=course).count()
        if total_slides > 0:
            completed_slides = StudentAnswer.objects.filter(
                slide__chasi__subject=course
            ).values('slide').distinct().count()
            progress = (completed_slides / total_slides * 100)
            total_progress += progress
            course_count += 1
    
    stats['avg_course_progress'] = round(total_progress / course_count, 1) if course_count > 0 else 0
    
    # 최근 데이터들
    recent_courses = Course.objects.filter(teacher=teacher).order_by('-created_at')[:5]
    recent_students = Student.objects.filter(
        school_class__teachers=teacher
    ).select_related('user', 'school_class').order_by('-created_at').distinct()[:5]
    
    # 최근 생성된 반 (새로 추가)
    recent_classes = Class.objects.filter(teachers=teacher).annotate(
        student_count=Count('student')
    ).order_by('-id')[:5]  # created_at이 없다면 id로 정렬
    
    # 최근 할당
    recent_assignments = CourseAssignment.objects.filter(
        course__teacher=teacher
    ).select_related('course', 'assigned_class', 'assigned_student').order_by('-assigned_at')[:10]
    
    context = {
        'stats': stats,
        'recent_courses': recent_courses,
        'recent_students': recent_students,
        'recent_classes': recent_classes,  # 새로 추가
        'recent_assignments': recent_assignments,
    }
    
    return render(request, 'teacher/dashboard.html', context)

@login_required
@teacher_required
def dashboard_view_0619(request):
    """교사 대시보드"""
    teacher = request.user.teacher
    
    # 통계 데이터
    stats = get_teacher_dashboard_stats(teacher)
    
    # 최근 생성된 코스들
    recent_courses = Course.objects.filter(teacher=teacher).order_by('-created_at')[:5]

    # ★★★ [수정] 교사가 속한 학급의 학생들을 가져오도록 변경 ★★★
    recent_students = Student.objects.filter(
        school_class__teachers=teacher
    ).select_related('user', 'school_class').order_by('-created_at')[:5]
    
    # # 최근 등록된 학생들
    # recent_students = Student.objects.filter(
    #     school_class__teacher=teacher
    # ).select_related('user', 'school_class').order_by('-created_at')[:5]
    
    # 최근 할당 - assigned_date를 assigned_at으로 변경
    recent_assignments = CourseAssignment.objects.filter(
        course__teacher=teacher
    ).select_related('course', 'assigned_class', 'assigned_student').order_by('-assigned_at')[:10]
    
    context = {
        'stats': stats,
        'recent_courses': recent_courses,
        'recent_students': recent_students,
        'recent_assignments': recent_assignments,
    }
    
    return render(request, 'teacher/dashboard.html', context)

# ========================================
# 앱들의 홈
# ========================================

@login_required
def app_home(request):
    """교사용 체육 앱 관리센터 홈페이지"""
    if not hasattr(request.user, 'teacher'):
        return JsonResponse({'error': '교사만 접근 가능합니다.'}, status=403)
    
    teacher = request.user.teacher
    teacher_classes = teacher.classes.all()
    
    # 최근 건강습관 실천기록장 슬라이드 가져오기
    # Chasi는 Course(subject)를 통해 teacher와 연결됨
    recent_health_slides = ChasiSlide.objects.filter(
        chasi__subject__teacher=teacher,
        content_type__type_name='take-action'  # 또는 적절한 콘텐츠 타입명
    ).select_related(
        'chasi__subject',
        'content_type',
        'content'
    ).order_by('-created_at')[:5]
    print("recent_health_sliders:",recent_health_slides)
    
    context = {
        'teacher': teacher,
        'teacher_classes': teacher_classes,
        'recent_health_slides': recent_health_slides,
    }
    
    return render(request, 'teacher/app_home.html', context)


@login_required
def get_slides_api(request):
    """슬라이드 목록을 반환하는 API"""
    if not hasattr(request.user, 'teacher'):
        return JsonResponse({'error': '교사만 접근 가능합니다.'}, status=403)
    
    teacher = request.user.teacher
    slide_type = request.GET.get('type', 'health')
    
    if slide_type == 'health':
        slides = ChasiSlide.objects.filter(
            chasi__subject__teacher=teacher,
            content_type__type_name__icontains='건강'  # 또는 적절한 필터
        ).select_related(
            'chasi__subject',
            'content_type'
        ).order_by('-created_at')[:20]
        
        slide_data = []
        for slide in slides:
            slide_data.append({
                'id': slide.id,
                'title': slide.chasi.chasi_title,  # chasi_title이 올바른 필드명
                'course_name': slide.chasi.subject.subject_name,  # 코스명
                'date': slide.created_at.strftime('%Y-%m-%d'),
            })
        
        return JsonResponse({'slides': slide_data})
    
    return JsonResponse({'slides': []})

# ========================================
# 코스 대시보드 뷰
# ========================================
@login_required
@teacher_required
def course_dashboard_view(request):
    """교사 코스 대시보드 (수정된 버전)"""
    teacher = request.user.teacher
    
    # 통계 데이터 (이전에 수정한 get_teacher_dashboard_stats 함수를 호출)
    stats = get_teacher_dashboard_stats(teacher)
    
    # 최근 생성된 코스들
    recent_courses = Course.objects.filter(teacher=teacher).order_by('-created_at')[:5]
    
    # ★★★ [수정] 교사가 속한 학급의 학생들을 가져오도록 변경 ★★★
    recent_students = Student.objects.filter(
        school_class__teachers=teacher
    ).select_related('user', 'school_class').order_by('-created_at').distinct()[:5]
    
    # 최근 할당
    recent_assignments = CourseAssignment.objects.filter(
        course__teacher=teacher
    ).select_related('course', 'assigned_class', 'assigned_student').order_by('-assigned_at')[:10]
    
    context = {
        'stats': stats,
        'recent_courses': recent_courses,
        'recent_students': recent_students,
        'recent_assignments': recent_assignments,
    }
    
    return render(request, 'teacher/dashboard_0530.html', context)

@login_required
@teacher_required
def course_dashboard_view_0608(request):
    """교사코스대시보드"""
    teacher = request.user.teacher
    
    # 통계 데이터
    stats = get_teacher_dashboard_stats(teacher)
    
    # 최근 생성된 코스들
    recent_courses = Course.objects.filter(teacher=teacher).order_by('-created_at')[:5]
    
    # 최근 등록된 학생들
    recent_students = Student.objects.filter(
        school_class__teacher=teacher
    ).select_related('user', 'school_class').order_by('-created_at')[:5]
    
    # 최근 할당
    recent_assignments = CourseAssignment.objects.filter(
        course__teacher=teacher
    ).select_related('course', 'assigned_class', 'assigned_student').order_by('-assigned_at')[:10]
    
    context = {
        'stats': stats,
        'recent_courses': recent_courses,
        'recent_students': recent_students,
        'recent_assignments': recent_assignments,
    }
    
    return render(request, 'teacher/dashboard_0530.html', context)
# ========================================
# 학급 관리 뷰들
# ========================================

@login_required
@teacher_required
def class_list_view(request):
    """학급 목록"""
    teacher = request.user.teacher
    # ★★★ [수정] 교사가 속한 학급을 'teachers' ManyToManyField로 필터링 ★★★
    classes = Class.objects.filter(teachers=teacher).annotate(
        student_count=Count('student')
    ).order_by('name')
    
    context = {
        'classes': classes,
    }
    
    return render(request, 'teacher/classes/list.html', context)

@login_required
@teacher_required
def class_create_view(request):
    """학급 생성"""
    teacher = request.user.teacher
    
    if request.method == 'POST':
        form = ClassCreateForm(request.POST)
        if form.is_valid():
            try:
                # ★★★ [수정] 데이터베이스 변경을 하나의 단위로 묶음 ★★★
                with transaction.atomic():
                    # 1. 먼저 Class 객체를 생성합니다. (teacher 필드 없이)
                    new_class = Class.objects.create(
                        school=teacher.school,
                        grade=form.cleaned_data['grade'],
                        class_number=form.cleaned_data['class_number'],
                        name=form.cleaned_data['name']
                    )
                    
                    # 2. 생성된 학급에 현재 교사를 '담임 교사' 역할로 배정합니다.
                    ClassTeacher.objects.create(
                        class_instance=new_class,
                        teacher=teacher,
                        role=ClassTeacher.RoleChoices.MAIN_TEACHER
                    )
                    
                messages.success(request, f'"{new_class.name}" 학급이 생성되고, 담임교사로 배정되었습니다.')
                return redirect('teacher:class_detail', class_id=new_class.id)

            except Exception as e:
                messages.error(request, f'학급 생성 중 오류가 발생했습니다: {str(e)}')
    else:
        form = ClassCreateForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'teacher/classes/create.html', context)

@login_required
@teacher_required
def class_detail_view(request, class_id):
    """학급 상세"""
    teacher = request.user.teacher
    # ★★★ [수정] teacher=teacher를 teachers=teacher로 변경 ★★★
    # 현재 로그인한 교사가 해당 학급에 배정되어 있는지 확인합니다.
    school_class = get_object_or_404(Class, id=class_id, teachers=teacher)
    students = Student.objects.filter(school_class=school_class).select_related('user')
    
    context = {
        'class': school_class,
        'students': students,
    }
    
    return render(request, 'teacher/classes/detail.html', context)

# ========================================
# 학생 관리 뷰들
# ========================================
@login_required
@teacher_required
def student_list_view(request):
    """학생 목록 (수정된 버전)"""
    teacher = request.user.teacher
    
    classes = Class.objects.filter(teachers=teacher).annotate(
        student_count=Count('student')
    ).order_by('name')
    
    selected_class_id = request.GET.get('class_id')
    selected_class = None
    students_queryset = Student.objects.none() 
    
    if selected_class_id:
        try:
            selected_class = Class.objects.get(id=selected_class_id, teachers=teacher)
        except Class.DoesNotExist:
            messages.error(request, '선택한 학급을 찾을 수 없거나 접근 권한이 없습니다.')
            if classes.exists():
                # 오류 발생 시, 교사의 첫 번째 학급으로 리다이렉트
                return redirect(f"{reverse('teacher:student_list')}?class_id={classes.first().id}")
    elif classes.exists():
        # 기본적으로 첫 번째 학급을 선택
        selected_class = classes.first()
    
    if selected_class:
        students_queryset = Student.objects.filter(school_class=selected_class).select_related('user')

    search_query = request.GET.get('search', '').strip()
    if search_query and selected_class:
        students_queryset = students_queryset.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(student_id__icontains=search_query)
        ).distinct()
    
    students_queryset = students_queryset.order_by('student_id')
    
    paginator = Paginator(students_queryset, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'classes': classes,
        'selected_class': selected_class,
        'students': page_obj,
        'search_query': search_query,
        'total_students': Student.objects.filter(school_class__teachers=teacher).distinct().count(),
        'class_student_count': students_queryset.count(),
    }
    
    return render(request, 'teacher/students/list.html', context)


@login_required
@teacher_required
def student_list_view_0609(request):
    """학생 목록 (수정된 버전)"""
    teacher = request.user.teacher
    
    # ★★★ [수정] 교사가 속한 학급을 'teachers' ManyToManyField로 필터링 ★★★
    classes = Class.objects.filter(teachers=teacher).order_by('name')
    
    # 선택된 학급
    selected_class_id = request.GET.get('class_id')
    selected_class = None
    
    # student_list 변수를 students로 통일하여 혼선 방지
    students_queryset = Student.objects.none() 
    
    if selected_class_id:
        try:
            # ★★★ [수정] 특정 학급을 가져올 때도 'teachers'로 교사 소유권 확인 ★★★
            selected_class = Class.objects.get(id=selected_class_id, teachers=teacher)
            students_queryset = Student.objects.filter(school_class=selected_class).select_related('user')
        except Class.DoesNotExist:
            messages.error(request, '선택한 학급을 찾을 수 없거나 접근 권한이 없습니다.')
            # 오류 발생 시, 교사의 첫 번째 학급을 기본값으로 설정
            if classes.exists():
                selected_class = classes.first()
                students_queryset = Student.objects.filter(school_class=selected_class).select_related('user')
    elif classes.exists():
        # 기본적으로 첫 번째 학급을 선택
        selected_class = classes.first()
        students_queryset = Student.objects.filter(school_class=selected_class).select_related('user')
    
    # 검색 기능
    search_query = request.GET.get('search', '').strip()
    if search_query and selected_class:
        students_queryset = students_queryset.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(student_id__icontains=search_query) |
            Q(user__username__icontains=search_query)
        ).distinct()
    
    students_queryset = students_queryset.order_by('student_id')
    
    # 페이지네이션
    paginator = Paginator(students_queryset, 15) # 한 페이지에 15명씩
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'classes': classes,
        'selected_class': selected_class,
        'students': page_obj, # Paginator의 page_obj를 students로 전달
        'search_query': search_query,
        'total_students': Student.objects.filter(school_class__teachers=teacher).distinct().count(),
        'class_student_count': students_queryset.count(),
    }
    
    return render(request, 'teacher/students/list.html', context)


@login_required
@teacher_required
def student_list_view_0608(request):
    """학생 목록"""
    teacher = request.user.teacher
    
    # 교사의 모든 학급
    classes = Class.objects.filter(teacher=teacher).order_by('name')
    
    # 선택된 학급
    selected_class_id = request.GET.get('class_id')
    selected_class = None
    students = Student.objects.none()
    
    if selected_class_id:
        try:
            selected_class = Class.objects.get(id=selected_class_id, teacher=teacher)
            students = Student.objects.filter(school_class=selected_class).select_related('user')
        except Class.DoesNotExist:
            messages.error(request, '선택한 학급을 찾을 수 없습니다.')
    elif classes.exists():
        selected_class = classes.first()
        students = Student.objects.filter(school_class=selected_class).select_related('user')
    
    # 검색 기능
    search_query = request.GET.get('search', '')
    if search_query and students.exists():
        students = students.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(student_id__icontains=search_query) |
            Q(user__username__icontains=search_query)
        )
    
    students = students.order_by('student_id')
    
    # 페이지네이션
    paginator = Paginator(students, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'classes': classes,
        'selected_class': selected_class,
        'selected_class_id': int(selected_class_id) if selected_class_id else None,
        'students': page_obj.object_list,
        'page_obj': page_obj,
        'search_query': search_query,
        'total_students': Student.objects.filter(school_class__teachers=teacher).count(),
        'class_student_count': students.count() if selected_class else 0,
    }
    
    return render(request, 'teacher/students/list.html', context)

@login_required
@teacher_required
def bulk_student_create_from_csv_view(request):
    """ CSV 파일을 업로드하여 여러 학생을 한번에 생성하는 뷰 (개선된 버전) """
    teacher = request.user.teacher
    classes = Class.objects.filter(teachers=teacher)
    context = {'classes': classes}

    if request.method != 'POST':
        return render(request, 'teacher/students/bulk_create_csv.html', context)

    class_id = request.POST.get('class_id')
    csv_file = request.FILES.get('student_file')

    if not class_id or not csv_file:
        messages.error(request, "학급과 CSV 파일을 모두 선택해주세요.")
        return redirect('teacher:bulk_student_create_from_csv')
        
    if not csv_file.name.endswith('.csv'):
        messages.error(request, "CSV 파일만 업로드할 수 있습니다.")
        return redirect('teacher:bulk_student_create_from_csv')

    try:
        target_class = Class.objects.get(id=class_id, teachers=teacher)
        
        # CSV 파일 파싱
        decoded_file = csv_file.read().decode('utf-8-sig').splitlines()
        reader = csv.reader(decoded_file)
        
        students_to_create = list(reader)
        success_count = 0
        fail_list = []

        with transaction.atomic():
            for i, row in enumerate(students_to_create):
                line_num = i + 2
                
                # 행의 데이터 개수 확인
                if len(row) < 3:
                    fail_list.append(f"<li>{line_num}번 줄: 데이터 부족 (이름,학번,비번 필요)</li>")
                    continue
                
                name, student_id, password = row[0].strip(), row[1].strip(), row[2].strip()
                
                if not all([name, student_id, password]):
                    fail_list.append(f"<li>{line_num}번 줄 ({name}): 필수 정보 누락</li>")
                    continue

                # 로그인 ID 형식: 학교코드_학번
                full_username = f"{teacher.school.code}_{student_id}"
                
                # ★★★ 같은 학교, 같은 학번(username)이 존재하면 건너뛰기 ★★★
                if User.objects.filter(username=full_username).exists():
                    fail_list.append(f"<li>{line_num}번 줄 ({name}, {student_id}): 이미 등록된 학번</li>")
                    continue

                # 위에서 걸러지지 않은 모든 학생은 생성 시도
                try:
                    user = User.objects.create_user(
                        username=full_username,
                        password=password,
                        first_name=name[1:] if len(name) > 1 else '',
                        last_name=name[0]
                    )
                    Student.objects.create(
                        user=user,
                        school_class=target_class,
                        student_id=student_id,
                        birth_date='2010-01-01' # 기본 생년월일
                    )
                    success_count += 1
                except Exception as e:
                    fail_list.append(f"<li>{line_num}번 줄 ({name}): DB 저장 오류 - {e}</li>")
        
        # 처리 결과에 따라 메시지 추가
        if success_count > 0:
            messages.success(request, f"총 {success_count}명의 학생을 성공적으로 등록했습니다.")
        if fail_list:
            error_details = "<ul>" + "".join(fail_list) + "</ul>"
            messages.warning(request, mark_safe(f"일부 학생 등록에 실패했습니다:<br>{error_details}"))
        elif success_count == 0:
            messages.info(request, "새롭게 등록된 학생이 없습니다. 업로드한 명단을 확인해주세요.")

        # ★★★ 성공/실패 여부와 관계없이 해당 학급 목록 페이지로 리다이렉트 ★★★
        redirect_url = f"{reverse('teacher:student_list')}?class_id={class_id}"
        return HttpResponseRedirect(redirect_url)

    except Class.DoesNotExist:
        messages.error(request, "선택한 학급을 찾을 수 없습니다.")
    except Exception as e:
        messages.error(request, f"파일 처리 중 오류가 발생했습니다: {e}")

    return redirect('teacher:bulk_student_create_from_csv')



@login_required
@teacher_required
def bulk_student_create_from_csv_view_0608(request):
    """ CSV 파일을 업로드하여 여러 학생을 한번에 생성하는 뷰 """
    teacher = request.user.teacher
    classes = Class.objects.filter(teacher=teacher)

    if request.method == 'POST':
        class_id = request.POST.get('class_id')
        csv_file = request.FILES.get('student_file')

        if not class_id or not csv_file:
            messages.error(request, "학급과 CSV 파일을 모두 선택해주세요.")
            return redirect('teacher:bulk_student_create_from_csv')
            
        if not csv_file.name.endswith('.csv'):
            messages.error(request, "CSV 파일만 업로드할 수 있습니다.")
            return redirect('teacher:bulk_student_create_from_csv')

        try:
            target_class = Class.objects.get(id=class_id, teacher=teacher)
            
            # CSV 파일 파싱
            decoded_file = csv_file.read().decode('utf-8-sig').splitlines()
            reader = csv.reader(decoded_file)
            
            # 헤더 건너뛰기 (선택사항, 첫 줄이 헤더일 경우)
            # next(reader, None) 
            
            students_to_create = list(reader)
            success_count = 0
            fail_list = []

            with transaction.atomic():
                for i, row in enumerate(students_to_create):
                    line_num = i + 1
                    if len(row) < 3:
                        fail_list.append(f"{line_num}번 줄: 데이터 부족 (이름,학번,비번 필요)")
                        continue
                    
                    name, student_id, password = row[0].strip(), row[1].strip(), row[2].strip()
                    
                    if not all([name, student_id, password]):
                        fail_list.append(f"{line_num}번 줄 ({name}): 필수 정보 누락")
                        continue

                    full_username = f"{teacher.school.code}_{student_id}"
                    
                    if User.objects.filter(username=full_username).exists():
                        fail_list.append(f"{line_num}번 줄 ({name}): 이미 존재하는 아이디")
                        continue

                    try:
                        user = User.objects.create_user(
                            username=full_username, password=password,
                            first_name=name[1:], last_name=name[0]
                        )
                        Student.objects.create(
                            user=user, school_class=target_class,
                            student_id=student_id, birth_date='2010-01-01'
                        )
                        success_count += 1
                    except Exception as e:
                        fail_list.append(f"{line_num}번 줄 ({name}): DB 저장 오류 - {e}")
            
            if success_count > 0:
                messages.success(request, f"총 {success_count}명의 학생을 성공적으로 등록했습니다.")
            if fail_list:
                 messages.warning(request, f"일부 학생 등록에 실패했습니다: {', '.join(fail_list)}")

            return redirect('teacher:student_list', class_id=class_id)

        except Class.DoesNotExist:
            messages.error(request, "선택한 학급을 찾을 수 없습니다.")
        except Exception as e:
            messages.error(request, f"파일 처리 중 오류가 발생했습니다: {e}")

    return render(request, 'teacher/students/bulk_create_csv.html', {'classes': classes})


@login_required
@teacher_required
def download_sample_csv_view(request):
    """학생 등록용 샘플 CSV 파일을 다운로드하는 뷰"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="student_sample.csv"'
    
    # UTF-8 BOM 추가하여 Excel에서 한글 깨짐 방지
    response.write(u'\ufeff'.encode('utf8'))

    writer = csv.writer(response)
    writer.writerow(['이름', '학번', '초기비밀번호'])
    writer.writerow(['김철수', '20250101', 'password123'])
    writer.writerow(['이영희', '20250102', 'password456'])
    
    return response


@login_required
@teacher_required
def student_create_view(request):
    """학생 등록 (수정된 버전)"""
    teacher = request.user.teacher
    teacher_classes = Class.objects.filter(teachers=teacher)

    if request.method == 'POST':
        form = StudentCreateForm(request.POST)
        form.fields['school_class'].queryset = teacher_classes

        if form.is_valid():
            try:
                with transaction.atomic():
                    class_obj = form.cleaned_data['school_class']
                    student_id = form.cleaned_data['student_id']
                    
                    if teacher not in class_obj.teachers.all():
                        messages.error(request, '해당 학급에 학생을 추가할 권한이 없습니다.')
                        # form을 context에 담아 다시 렌더링
                        return render(request, 'teacher/students/create.html', {'form': form, 'school_code': teacher.school.code})

                    username = f"{teacher.school.code}_{student_id}"
                    if User.objects.filter(username=username).exists():
                        messages.error(request, f'이미 등록된 학번입니다: {student_id}')
                        return render(request, 'teacher/students/create.html', {'form': form, 'school_code': teacher.school.code})
                    
                    user = User.objects.create_user(
                        username=username,
                        password=form.cleaned_data['password'],
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name'],
                        email=form.cleaned_data.get('email', '')
                    )
                    
                    Student.objects.create(
                        user=user, school_class=class_obj,
                        student_id=student_id, birth_date=form.cleaned_data['birth_date']
                    )
                    
                    messages.success(request, f'"{user.get_full_name()}" 학생이 성공적으로 등록되었습니다.')
                    # ★★★ [수정] 올바른 redirect 방식 ★★★
                    redirect_url = f"{reverse('teacher:student_list')}?class_id={class_obj.id}"
                    return redirect(redirect_url)
                    
            except Exception as e:
                messages.error(request, f'학생 등록 중 오류가 발생했습니다: {str(e)}')
    else:
        # GET 요청 시
        form = StudentCreateForm(initial=request.GET)
        form.fields['school_class'].queryset = teacher_classes

    context = {
        'form': form,
        'school_code': teacher.school.code,
    }
    return render(request, 'teacher/students/create.html', context)


@login_required
@teacher_required
def student_create_view_0608(request):
    """학생 등록"""
    teacher = request.user.teacher
    
    if request.method == 'POST':
        form = StudentCreateForm(request.POST)
        # ★★★ [수정] 교사가 속한 학급만 선택지에 나타나도록 폼의 queryset을 먼저 필터링 ★★★
        form.fields['school_class'].queryset = Class.objects.filter(teachers=teacher)

        if form.is_valid():
            try:
                with transaction.atomic():
                    # 기본 정보 가져오기
                    class_obj = form.cleaned_data['school_class']
                    student_id = form.cleaned_data['student_id']
                    first_name = form.cleaned_data['first_name']
                    last_name = form.cleaned_data['last_name']
                    birth_date = form.cleaned_data['birth_date']
                    email = form.cleaned_data['email']
                    password = form.cleaned_data['password']
                    
                    # 학급이 해당 교사의 것인지 확인
                    if class_obj.teacher != teacher:
                        messages.error(request, '해당 학급에 접근할 권한이 없습니다.')
                        return render(request, 'teacher/students/create.html', {'form': form})
                    
                    # 학교 코드 가져오기
                    school_code = teacher.school.code if hasattr(teacher, 'school') else 'SC001'
                    
                    # 사용자명 생성: 학교코드_학번
                    username = f"{school_code}_{student_id}"
                    
                    # 중복 확인
                    if User.objects.filter(username=username).exists():
                        messages.error(request, f'이미 등록된 학번입니다: {student_id}')
                        return render(request, 'teacher/students/create.html', {'form': form})
                    
                    # User 계정 생성
                    user = User.objects.create_user(
                        username=username,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        email=email
                    )
                    
                    # Student 정보 생성
                    student = Student.objects.create(
                        user=user,
                        school_class=class_obj,
                        student_id=student_id,
                        birth_date=birth_date
                    )
                    
                    messages.success(request, f'{user.get_full_name()} 학생이 성공적으로 등록되었습니다.')
                    return redirect('teacher:student_list')
                    
            except Exception as e:
                messages.error(request, f'학생 등록 중 오류가 발생했습니다: {str(e)}')
    else:
        # 선택된 학급이 있는 경우 초기값 설정
        selected_class_id = request.GET.get('class_id')
        initial_data = {}
        
        if selected_class_id:
            try:
                selected_class = Class.objects.get(id=selected_class_id, teachers=teacher)
                initial_data['school_class'] = selected_class
                
                # 다음 학번 제안
                last_student = Student.objects.filter(
                    school_class=selected_class
                ).order_by('-student_id').first()
                
                if last_student:
                    try:
                        last_num = int(last_student.student_id[-3:])
                        suggested_id = f"{last_student.student_id[:-3]}{str(last_num + 1).zfill(3)}"
                        initial_data['student_id'] = suggested_id
                    except:
                        year = datetime.now().year
                        initial_data['student_id'] = f"{year}{str(selected_class_id).zfill(2)}001"
                else:
                    year = datetime.now().year
                    initial_data['student_id'] = f"{year}{str(selected_class_id).zfill(2)}001"
            except Class.DoesNotExist:
                pass
        
        form = StudentCreateForm(initial=initial_data)
        # 교사의 학급만 선택 가능하도록 제한
        form.fields['school_class'].queryset = Class.objects.filter(teacher=teacher)
    
    # 컨텍스트에 추가 정보
    context = {
        'form': form,
        'school_code': teacher.school.code if hasattr(teacher, 'school') else 'SC001',
    }
    
    return render(request, 'teacher/students/create.html', context)

@login_required
@teacher_required
def student_detail_view(request, student_id):
    """학생 상세 정보"""
    teacher = request.user.teacher
    # ★★★ [수정] school_class__teacher -> school_class__teachers 로 변경 ★★★
    # 교사가 해당 학생의 학급에 속해있는지 확인합니다.
    student = get_object_or_404(
        Student.objects.select_related('user', 'school_class'),
        id=student_id,
        school_class__teachers=teacher
    )
    
    context = {
        'student': student,
    }
    
    return render(request, 'teacher/students/detail.html', context)

@login_required
@teacher_required
def student_edit_view(request, student_id):
    """학생 정보 수정"""
    teacher = request.user.teacher
    # ★★★ [수정] school_class__teacher -> school_class__teachers 로 변경 ★★★
    student = get_object_or_404(
        Student.objects.select_related('user', 'school_class'),
        id=student_id,
        school_class__teachers=teacher
    )
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # User 정보 업데이트
                student.user.first_name = request.POST.get('first_name')
                student.user.last_name = request.POST.get('last_name')
                student.user.email = request.POST.get('email', '')
                student.user.save()
                
                # Student 정보 업데이트
                birth_date = request.POST.get('birth_date')
                if birth_date:
                    student.birth_date = birth_date
                
                # 학급 변경 (동일 교사의 학급만 가능)
                new_class_id = request.POST.get('class_id')
                if new_class_id and str(student.school_class.id) != new_class_id:
                    # ★★★ [수정] teacher=teacher -> teachers=teacher 로 변경 ★★★
                    new_class = get_object_or_404(Class, id=new_class_id, teachers=teacher)
                    student.school_class = new_class
                
                student.save()
                
                messages.success(request, f'{student.user.get_full_name()} 학생 정보가 수정되었습니다.')
                return redirect('teacher:student_detail', student_id=student.id)
                
        except Exception as e:
            messages.error(request, f'정보 수정 중 오류가 발생했습니다: {str(e)}')
    
    # ★★★ [수정] 교사가 속한 학급 목록만 가져오도록 변경 ★★★
    classes = Class.objects.filter(teachers=teacher)
    context = {
        'student': student,
        'classes': classes,
    }
    
    return render(request, 'teacher/students/edit.html', context)

@login_required
@teacher_required
def student_delete_view(request, student_id):
    """학생 삭제 (수정된 버전)"""
    teacher = request.user.teacher
    
    # ★★★ [수정] school_class__teacher -> school_class__teachers 로 변경 ★★★
    # 현재 로그인한 교사가 해당 학생의 학급에 속해있는지 확인합니다.
    student = get_object_or_404(
        Student.objects.select_related('user'),
        id=student_id,
        school_class__teachers=teacher
    )
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                student_name = student.user.get_full_name()
                # User와 Student 모두 삭제 (User를 삭제하면 Student는 자동으로 삭제됩니다)
                student.user.delete()  
                
                messages.success(request, f'"{student_name}" 학생이 삭제되었습니다.')
                return redirect('teacher:student_list')
                
        except Exception as e:
            messages.error(request, f'학생 삭제 중 오류가 발생했습니다: {str(e)}')
    
    context = {
        'student': student,
    }
    
    return render(request, 'teacher/students/delete_confirm.html', context)


@login_required
@teacher_required
def student_delete_view_0608(request, student_id):
    """학생 삭제"""
    teacher = request.user.teacher
    student = get_object_or_404(
        Student.objects.select_related('user'),
        id=student_id,
        school_class__teacher=teacher
    )
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                student_name = student.user.get_full_name()
                # User와 Student 모두 삭제
                student.user.delete()  # CASCADE로 Student도 삭제됨
                
                messages.success(request, f'{student_name} 학생이 삭제되었습니다.')
                return redirect('teacher:student_list')
                
        except Exception as e:
            messages.error(request, f'학생 삭제 중 오류가 발생했습니다: {str(e)}')
    
    context = {
        'student': student,
    }
    
    return render(request, 'teacher/students/delete_confirm.html', context)

# teacher/views.py에서 다음 함수들을 교체하세요:

@login_required
@teacher_required
def student_reset_password_view(request, student_id):
    """학생 비밀번호 초기화 (수정된 버전)"""
    teacher = request.user.teacher
    # ★★★ [수정] school_class__teacher -> school_class__teachers 로 변경 ★★★
    student = get_object_or_404(
        Student.objects.select_related('user'),
        id=student_id,
        school_class__teachers=teacher  # 이 부분이 핵심!
    )
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        if new_password and len(new_password) >= 8:
            try:
                student.user.set_password(new_password)
                student.user.save()
                messages.success(request, f'{student.user.get_full_name()} 학생의 비밀번호가 초기화되었습니다.')
                return redirect('teacher:student_detail', student_id=student.id)
            except Exception as e:
                messages.error(request, f'비밀번호 초기화 중 오류가 발생했습니다: {str(e)}')
        else:
            messages.error(request, '비밀번호는 8자 이상이어야 합니다.')
    
    context = {
        'student': student,
    }
    
    return render(request, 'teacher/students/reset_password.html', context)

@login_required
@teacher_required
@require_http_methods(["GET"])
def api_class_students(request, class_id):
    """특정 학급의 학생 목록 API (수정된 버전)"""
    teacher = request.user.teacher
    
    try:
        # ★★★ [수정] teacher=teacher -> teachers=teacher 로 변경 ★★★
        class_obj = Class.objects.get(id=class_id, teachers=teacher)
        students = Student.objects.filter(school_class=class_obj).select_related('user')
        
        students_data = []
        for student in students:
            students_data.append({
                'id': student.id,
                'name': student.user.get_full_name(),
                'student_id': student.student_id,
                'username': student.user.username,
            })
        
        return JsonResponse({
            'success': True,
            'class_name': class_obj.name,
            'students': students_data
        })
    
    except Class.DoesNotExist:
        return JsonResponse({'success': False, 'error': '학급을 찾을 수 없습니다.'}, status=404)

@login_required
@teacher_required
@require_http_methods(["GET"])
def api_student_search(request):
    """학생 검색 API (수정된 버전)"""
    teacher = request.user.teacher
    query = request.GET.get('q', '')
    class_id = request.GET.get('class_id')
    
    # ★★★ [수정] school_class__teacher -> school_class__teachers 로 변경 ★★★
    students = Student.objects.filter(school_class__teachers=teacher)
    
    if class_id:
        students = students.filter(school_class_id=class_id)
    
    if query:
        students = students.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(student_id__icontains=query)
        )
    
    students_data = []
    for student in students[:10]:  # 최대 10개만 반환
        students_data.append({
            'id': student.id,
            'name': student.user.get_full_name(),
            'student_id': student.student_id,
            'class_name': student.school_class.name,
        })
    
    return JsonResponse({'students': students_data})

@login_required
@teacher_required
def statistics_view(request):
    """통계 및 분석 (수정된 버전)"""
    teacher = request.user.teacher
    
    # 기본 통계
    stats = get_teacher_dashboard_stats(teacher)
    
    # ★★★ [수정] 학급별 학생 수 - teachers 필드 사용 ★★★
    class_stats = Class.objects.filter(teachers=teacher).annotate(
        student_count=Count('student')
    ).values('name', 'student_count')
    
    # 코스별 할당 수
    course_stats = Course.objects.filter(teacher=teacher).annotate(
        assignment_count=Count('courseassignment')
    ).values('subject_name', 'assignment_count')
    
    context = {
        'stats': stats,
        'class_stats': list(class_stats),
        'course_stats': list(course_stats),
    }
    
    return render(request, 'teacher/statistics/index.html', context)

@csrf_exempt
@require_http_methods(["GET"])
def api_dashboard_stats(request):
    """대시보드 통계 API"""
    if not hasattr(request.user, 'teacher'):
        return JsonResponse({'error': '교사만 접근 가능합니다.'}, status=403)
    
    teacher = request.user.teacher
    stats = get_teacher_dashboard_stats(teacher)
    
    return JsonResponse(stats)


@login_required
@teacher_required  
def api_content_types(request):
    """콘텐츠 타입 목록 API"""
    content_types = ContentType.objects.filter(is_active=True)
    data = {
        'content_types': [
            {'id': ct.id, 'type_name': ct.type_name} 
            for ct in content_types
        ]
    }
    return JsonResponse(data)

@login_required
@teacher_required
def api_chapter_subchapters(request, chapter_id):
    """특정 대단원의 소단원 목록 API"""
    chapter = get_object_or_404(Chapter, id=chapter_id, subject__teacher=request.user.teacher)
    subchapters = SubChapter.objects.filter(chapter=chapter).order_by('sub_chapter_order')
    data = {
        'subchapters': [
            {'id': sc.id, 'title': sc.sub_chapter_title, 'order': sc.sub_chapter_order}
            for sc in subchapters
        ]
    }
    return JsonResponse(data)



@login_required
@teacher_required
def api_contents_search(request):
    """콘텐츠 검색 API"""
    try:
        teacher = request.user.teacher
        
        # 검색 파라미터 가져오기
        query = request.GET.get('q', '').strip()
        content_type_id = request.GET.get('content_type', '')
        chapter_id = request.GET.get('chapter', '')
        subchapter_id = request.GET.get('subchapter', '')
        course_id = request.GET.get('course_id', '')
        
        # 기본 쿼리셋 (활성화된 콘텐츠만)
        contents = Contents.objects.filter(is_active=True)
        
        # 교사의 콘텐츠만 (혹은 공개 콘텐츠)
        contents = contents.filter(
            Q(teacher=teacher) | Q(is_public=True)
        )
        
        # 텍스트 검색
        if query:
            contents = contents.filter(
                Q(title__icontains=query) |
                Q(page__icontains=query) |
                Q(tags__icontains=query)
            )
        
        # 콘텐츠 타입 필터
        if content_type_id:
            contents = contents.filter(content_type_id=content_type_id)
        
        # 대단원 필터
        if chapter_id:
            contents = contents.filter(chapter_id=chapter_id)
        
        # 소단원 필터
        if subchapter_id:
            contents = contents.filter(subchapter_id=subchapter_id)
        
        # 코스 필터 (대단원을 통해)
        # if course_id:
        #     contents = contents.filter(chapter__subject_id=course_id)
        
        # 정렬 및 제한
        contents = contents.select_related(
            'content_type', 'chapter', 'subchapter'
        ).order_by('-created_at')[:50]  # 최대 50개
        
        # 결과 직렬화
        results = []
        for content in contents:
            # 미리보기 텍스트 생성
            preview = ''
            if content.page:
                # HTML 태그 제거하고 첫 100자만
                import re
                preview = re.sub(r'<[^>]+>', '', content.page)[:100]
            
            results.append({
                'id': content.id,
                'title': content.title,
                'content_type': content.content_type.type_name if content.content_type else '',
                'content_type_display': content.content_type.type_name if content.content_type else '',
                'chapter_name': content.chapter.chapter_title if content.chapter else '',
                'subchapter_name': content.subchapter.sub_chapter_title if content.subchapter else '',
                'preview': preview,
                'created_at': content.created_at.strftime('%Y-%m-%d') if content.created_at else '',
                'difficulty': getattr(content, 'difficulty', ''),
                'estimated_time': getattr(content, 'estimated_time', 5),
            })
        
        return JsonResponse({
            'success': True,
            'results': results,
            'total': len(results)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    



@login_required
@teacher_required
def api_content_type_template(request, type_id):
    """콘텐츠 타입별 템플릿 반환 API"""
    try:
        content_type = get_object_or_404(ContentType, id=type_id, is_active=True)
        
        # 기본 템플릿들
        templates = {
            'multiple_choice': '''<div class="question">
    <h4>문제: 다음 중 올바른 것은?</h4>
    <ol type="1">
        <li>첫 번째 보기</li>
        <li>두 번째 보기</li>
        <li>세 번째 보기</li>
        <li>네 번째 보기</li>
    </ol>
</div>''',
            'short_answer': '''<div class="question">
    <h4>문제: 다음 빈칸에 알맞은 답을 쓰시오.</h4>
    <p>_________는 우리나라의 수도입니다.</p>
    <div class="answer-input">
        <label>답: <input type="text" name="answer" class="form-input" /></label>
    </div>
</div>''',
            'essay': '''<div class="question">
    <h4>문제: 다음 주제에 대해 서술하시오.</h4>
    <p>민주주의의 기본 원리에 대해 설명하시오. (200자 이상)</p>
    <div class="answer-input">
        <textarea name="answer" rows="10" class="form-textarea w-full" placeholder="답안을 작성하세요..."></textarea>
    </div>
</div>''',
            'presentation': '''<div class="presentation">
    <h3>프레젠테이션 제목</h3>
    <div class="slide">
        <h4>슬라이드 1</h4>
        <p>여기에 내용을 입력하세요.</p>
    </div>
</div>''',
            'default': '''<div class="content">
    <h4>제목</h4>
    <p>여기에 내용을 입력하세요.</p>
</div>'''
        }
        
        # 콘텐츠 타입명에 따라 템플릿 선택
        template = templates.get('default')
        type_name_lower = content_type.type_name.lower()
        
        if '객관식' in type_name_lower or 'multiple' in type_name_lower:
            template = templates['multiple_choice']
        elif '단답' in type_name_lower or 'short' in type_name_lower:
            template = templates['short_answer']
        elif '서술' in type_name_lower or 'essay' in type_name_lower:
            template = templates['essay']
        elif 'ppt' in type_name_lower or 'presentation' in type_name_lower:
            template = templates['presentation']
        
        return JsonResponse({
            'success': True,
            'template': template,
            'content_type': content_type.type_name
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)