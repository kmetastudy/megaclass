from django.db.models import Count, Max, Sum
from .models import Course, Chapter, SubChapter, Chasi, ChasiSlide, CourseAssignment
from accounts.models import Student,Class

def get_next_order(model, parent_field=None, parent_id=None, order_field=None):
    """다음 순서 번호를 반환하는 유틸리티 함수"""
    
    # order_field가 지정되지 않은 경우 모델에 따라 자동 결정
    if not order_field:
        if model == Chapter:
            order_field = 'chapter_order'
        elif model == SubChapter:
            order_field = 'sub_chapter_order'
        elif model == Chasi:
            order_field = 'chasi_order'
        elif model == ChasiSlide:
            order_field = 'slide_number'
        else:
            order_field = 'order'
    
    queryset = model.objects.all()
    
    # 부모 필드가 지정된 경우 필터링
    if parent_field and parent_id:
        filter_kwargs = {parent_field: parent_id}
        queryset = queryset.filter(**filter_kwargs)
    
    # 최대 순서 번호 조회
    last_obj = queryset.aggregate(max_order=Max(order_field))
    max_order = last_obj.get('max_order')
    
    return (max_order or 0) + 1

def get_course_statistics(course):
    """코스 통계 정보를 반환하는 함수"""
    try:
        # 대단원 수 - related_name='chapters' 사용
        total_chapters = course.chapters.count()
        
        # 소단원 수
        total_subchapters = SubChapter.objects.filter(chapter__subject=course).count()
        
        # 차시 수 - 수정: subchapter -> sub_chapter
        total_chasis = Chasi.objects.filter(
            sub_chapter__chapter__subject=course  # subchapter를 sub_chapter로 변경
        ).count()
        
        # 슬라이드 수 - 수정: subchapter -> sub_chapter
        total_slides = ChasiSlide.objects.filter(
            chasi__sub_chapter__chapter__subject=course  # subchapter를 sub_chapter로 변경
        ).count()
        
        # 할당된 학급 수 - CourseAssignment 모델 사용
        assigned_classes = CourseAssignment.objects.filter(
            course=course,
            assigned_class__isnull=False
        ).count()
        
        # 할당된 학생 수 - 개별 학생 할당 + 학급 할당된 학생들
        individual_students = CourseAssignment.objects.filter(
            course=course,
            assigned_student__isnull=False
        ).count()
        
        # 학급을 통해 할당된 학생 수
        class_students = 0
        class_assignments = CourseAssignment.objects.filter(
            course=course,
            assigned_class__isnull=False
        ).select_related('assigned_class')
        
        for assignment in class_assignments:
            class_students += assignment.get_student_count()
        
        assigned_students = individual_students + class_students
        
        # 총 예상 수업 시간 - 수정: subchapter -> sub_chapter
        total_duration = Chasi.objects.filter(
            sub_chapter__chapter__subject=course  # subchapter를 sub_chapter로 변경
        ).aggregate(
            total_time=Sum('duration_minutes')
        ).get('total_time') or 0
        
        return {
            'total_chapters': total_chapters,
            'total_subchapters': total_subchapters,
            'total_chasis': total_chasis,
            'total_slides': total_slides,
            'assigned_classes': assigned_classes,
            'assigned_students': assigned_students,
            'total_duration_minutes': total_duration,
            'total_duration_hours': round(total_duration / 60, 1) if total_duration else 0,
        }
        
    except Exception as e:
        # 디버깅을 위해 에러 로깅 추가
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in get_course_statistics: {str(e)}")
        
        # 오류가 발생한 경우 기본값 반환
        return {
            'total_chapters': 0,
            'total_subchapters': 0,
            'total_chasis': 0,
            'total_slides': 0,
            'assigned_classes': 0,
            'assigned_students': 0,
            'total_duration_minutes': 0,
            'total_duration_hours': 0,
        }

def get_course_progress(course):
    """코스 진행률을 계산하는 함수"""
    try:
        # 전체 차시 수 - 수정: subchapter -> sub_chapter
        total_chasis = Chasi.objects.filter(
            sub_chapter__chapter__subject=course  # subchapter를 sub_chapter로 변경
        ).count()
        
        if total_chasis == 0:
            return 0
        
        # 공개된 차시 수 - 수정: subchapter -> sub_chapter
        published_chasis = Chasi.objects.filter(
            sub_chapter__chapter__subject=course,  # subchapter를 sub_chapter로 변경
            is_published=True
        ).count()
        
        # 슬라이드가 있는 차시 수 - 수정: subchapter -> sub_chapter
        chasis_with_slides = Chasi.objects.filter(
            sub_chapter__chapter__subject=course  # subchapter를 sub_chapter로 변경
        ).annotate(
            slide_count=Count('teacher_slides')
        ).filter(slide_count__gt=0).count()
        
        # 진행률 계산 (공개된 차시와 슬라이드가 있는 차시의 평균)
        progress = ((published_chasis + chasis_with_slides) / (total_chasis * 2)) * 100
        
        return min(round(progress, 1), 100)  # 최대 100%로 제한
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in get_course_progress: {str(e)}")
        return 0

def get_course_statistics_0615(course):
    """코스 통계 정보를 반환하는 함수"""
    try:
        # 대단원 수 - related_name='chapters' 사용
        total_chapters = course.chapters.count()
        
        # 소단원 수
        total_subchapters = SubChapter.objects.filter(chapter__subject=course).count()
        
        # 차시 수
        total_chasis = Chasi.objects.filter(
            subchapter__chapter__subject=course
        ).count()
        
        # 슬라이드 수
        total_slides = ChasiSlide.objects.filter(
            chasi__subchapter__chapter__subject=course
        ).count()
        
        # 할당된 학급 수 - CourseAssignment 모델 사용
        assigned_classes = CourseAssignment.objects.filter(
            course=course,
            assigned_class__isnull=False
        ).count()
        
        # 할당된 학생 수 - 개별 학생 할당 + 학급 할당된 학생들
        individual_students = CourseAssignment.objects.filter(
            course=course,
            assigned_student__isnull=False
        ).count()
        
        # 학급을 통해 할당된 학생 수
        class_students = 0
        class_assignments = CourseAssignment.objects.filter(
            course=course,
            assigned_class__isnull=False
        ).select_related('assigned_class')
        
        for assignment in class_assignments:
            class_students += assignment.get_student_count()
        
        assigned_students = individual_students + class_students
        
        # 총 예상 수업 시간
        total_duration = Chasi.objects.filter(
            subchapter__chapter__subject=course
        ).aggregate(
            total_time=Sum('duration_minutes')
        ).get('total_time') or 0
        
        return {
            'total_chapters': total_chapters,
            'total_subchapters': total_subchapters,
            'total_chasis': total_chasis,
            'total_slides': total_slides,
            'assigned_classes': assigned_classes,
            'assigned_students': assigned_students,
            'total_duration_minutes': total_duration,
            'total_duration_hours': round(total_duration / 60, 1) if total_duration else 0,
        }
        
    except Exception as e:
        # 디버깅을 위해 에러 로깅 추가
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in get_course_statistics: {str(e)}")
        
        # 오류가 발생한 경우 기본값 반환
        return {
            'total_chapters': 0,
            'total_subchapters': 0,
            'total_chasis': 0,
            'total_slides': 0,
            'assigned_classes': 0,
            'assigned_students': 0,
            'total_duration_minutes': 0,
            'total_duration_hours': 0,
        }


def get_course_progress_0615(course):
    """코스 진행률을 계산하는 함수"""
    try:
        # 전체 차시 수
        total_chasis = Chasi.objects.filter(
            subchapter__chapter__subject=course
        ).count()
        
        if total_chasis == 0:
            return 0
        
        # 공개된 차시 수
        published_chasis = Chasi.objects.filter(
            subchapter__chapter__subject=course,
            is_published=True
        ).count()
        
        # 슬라이드가 있는 차시 수
        chasis_with_slides = Chasi.objects.filter(
            subchapter__chapter__subject=course
        ).annotate(
            slide_count=Count('teacher_slides')
        ).filter(slide_count__gt=0).count()
        
        # 진행률 계산 (공개된 차시와 슬라이드가 있는 차시의 평균)
        progress = ((published_chasis + chasis_with_slides) / (total_chasis * 2)) * 100
        
        return min(round(progress, 1), 100)  # 최대 100%로 제한
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in get_course_progress: {str(e)}")
        return 0


def get_course_statistics_0609(course):
    """코스 통계 정보를 반환하는 함수"""
    try:
        # 대단원 수
        total_chapters = Chapter.objects.filter(subject=course).count()
        
        # 소단원 수
        total_subchapters = SubChapter.objects.filter(subject=course).count()
        
        # 차시 수
        total_chasis = Chasi.objects.filter(subject=course).count()
        
        # 슬라이드 수
        total_slides = ChasiSlide.objects.filter(chasi__subject=course).count()
        
        # 할당된 학급 수
        assigned_classes = course.courseassignment_set.filter(
            assigned_class__isnull=False
        ).count()
        
        # 할당된 학생 수
        assigned_students = course.courseassignment_set.filter(
            assigned_student__isnull=False
        ).count()
        
        # 총 예상 수업 시간
        total_duration = Chasi.objects.filter(subject=course).aggregate(
            total_time=Sum('duration_minutes')
        ).get('total_time') or 0
        
        return {
            'total_chapters': total_chapters,
            'total_subchapters': total_subchapters,
            'total_chasis': total_chasis,
            'total_slides': total_slides,
            'assigned_classes': assigned_classes,
            'assigned_students': assigned_students,
            'total_duration_minutes': total_duration,
            'total_duration_hours': round(total_duration / 60, 1) if total_duration else 0,
        }
        
    except Exception as e:
        # 오류가 발생한 경우 기본값 반환
        return {
            'total_chapters': 0,
            'total_subchapters': 0,
            'total_chasis': 0,
            'total_slides': 0,
            'assigned_classes': 0,
            'assigned_students': 0,
            'total_duration_minutes': 0,
            'total_duration_hours': 0,
        }

def get_course_progress_0609(course):
    """코스 진행률을 계산하는 함수"""
    try:
        # 전체 차시 수
        total_chasis = Chasi.objects.filter(subject=course).count()
        
        if total_chasis == 0:
            return 0
        
        # 공개된 차시 수
        published_chasis = Chasi.objects.filter(
            subject=course,
            is_published=True
        ).count()
        
        # 슬라이드가 있는 차시 수
        chasis_with_slides = Chasi.objects.filter(
            subject=course
        ).annotate(
            slide_count=Count('teacher_slides')
        ).filter(slide_count__gt=0).count()
        
        # 진행률 계산 (공개된 차시와 슬라이드가 있는 차시의 평균)
        progress = ((published_chasis + chasis_with_slides) / (total_chasis * 2)) * 100
        
        return min(round(progress, 1), 100)  # 최대 100%로 제한
        
    except Exception as e:
        return 0

def get_chapter_statistics(chapter):
    """대단원 통계 정보를 반환하는 함수"""
    try:
        # 소단원 수
        total_subchapters = SubChapter.objects.filter(chapter=chapter).count()
        
        # 차시 수
        total_chasis = Chasi.objects.filter(chapter=chapter).count()
        
        # 슬라이드 수
        total_slides = ChasiSlide.objects.filter(chasi__chapter=chapter).count()
        
        # 총 예상 수업 시간
        total_duration = Chasi.objects.filter(chapter=chapter).aggregate(
            total_time=Sum('duration_minutes')
        ).get('total_time') or 0
        
        return {
            'total_subchapters': total_subchapters,
            'total_chasis': total_chasis,
            'total_slides': total_slides,
            'total_duration_minutes': total_duration,
            'total_duration_hours': round(total_duration / 60, 1) if total_duration else 0,
        }
        
    except Exception as e:
        return {
            'total_subchapters': 0,
            'total_chasis': 0,
            'total_slides': 0,
            'total_duration_minutes': 0,
            'total_duration_hours': 0,
        }

def get_subchapter_statistics(subchapter):
    """소단원 통계 정보를 반환하는 함수"""
    try:
        # 차시 수
        total_chasis = Chasi.objects.filter(sub_chapter=subchapter).count()
        
        # 슬라이드 수
        total_slides = ChasiSlide.objects.filter(chasi__sub_chapter=subchapter).count()
        
        # 총 예상 수업 시간
        total_duration = Chasi.objects.filter(sub_chapter=subchapter).aggregate(
            total_time=Sum('duration_minutes')
        ).get('total_time') or 0
        
        # 공개된 차시 수
        published_chasis = Chasi.objects.filter(
            sub_chapter=subchapter,
            is_published=True
        ).count()
        
        return {
            'total_chasis': total_chasis,
            'total_slides': total_slides,
            'published_chasis': published_chasis,
            'total_duration_minutes': total_duration,
            'total_duration_hours': round(total_duration / 60, 1) if total_duration else 0,
        }
        
    except Exception as e:
        return {
            'total_chasis': 0,
            'total_slides': 0,
            'published_chasis': 0,
            'total_duration_minutes': 0,
            'total_duration_hours': 0,
        }

def get_chasi_statistics(chasi):
    """차시 통계 정보를 반환하는 함수"""
    try:
        # 슬라이드 수
        total_slides = ChasiSlide.objects.filter(chasi=chasi).count()
        
        # 활성화된 슬라이드 수
        active_slides = ChasiSlide.objects.filter(
            chasi=chasi,
            is_active=True
        ).count()
        
        # 총 예상 시간 (슬라이드별 예상 시간의 합)
        total_estimated_time = ChasiSlide.objects.filter(chasi=chasi).aggregate(
            total_time=Sum('estimated_time')
        ).get('total_time') or 0
        
        return {
            'total_slides': total_slides,
            'active_slides': active_slides,
            'total_estimated_time': total_estimated_time,
            'completion_rate': round((active_slides / total_slides * 100), 1) if total_slides > 0 else 0,
        }
        
    except Exception as e:
        return {
            'total_slides': 0,
            'active_slides': 0,
            'total_estimated_time': 0,
            'completion_rate': 0,
        }
    

def validate_course_structure(course):
    """코스 구조의 유효성을 검사하는 함수"""
    errors = []
    warnings = []
    
    try:
        # 대단원이 없는 경우
        chapters = Chapter.objects.filter(subject=course)
        if not chapters.exists():
            errors.append("대단원이 없습니다.")
            return {'errors': errors, 'warnings': warnings}
        
        for chapter in chapters:
            # 소단원이 없는 대단원
            subchapters = SubChapter.objects.filter(chapter=chapter)
            if not subchapters.exists():
                warnings.append(f"대단원 '{chapter.chapter_title}'에 소단원이 없습니다.")
                continue
            
            for subchapter in subchapters:
                # 차시가 없는 소단원
                chasis = Chasi.objects.filter(sub_chapter=subchapter)  # subchapter를 sub_chapter로 변경
                if not chasis.exists():
                    warnings.append(f"소단원 '{subchapter.sub_chapter_title}'에 차시가 없습니다.")
                    continue
                
                for chasi in chasis:
                    # 슬라이드가 없는 차시
                    slides = ChasiSlide.objects.filter(chasi=chasi)
                    if not slides.exists():
                        warnings.append(f"차시 '{chasi.chasi_title}'에 슬라이드가 없습니다.")
        
        return {'errors': errors, 'warnings': warnings}
        
    except Exception as e:
        errors.append(f"구조 검사 중 오류가 발생했습니다: {str(e)}")
        return {'errors': errors, 'warnings': warnings}    

def validate_course_structure_0615(course):
    """코스 구조의 유효성을 검사하는 함수"""
    errors = []
    warnings = []
    
    try:
        # 대단원이 없는 경우
        chapters = Chapter.objects.filter(subject=course)
        if not chapters.exists():
            errors.append("대단원이 없습니다.")
            return {'errors': errors, 'warnings': warnings}
        
        for chapter in chapters:
            # 소단원이 없는 대단원
            subchapters = SubChapter.objects.filter(chapter=chapter)
            if not subchapters.exists():
                warnings.append(f"대단원 '{chapter.chapter_title}'에 소단원이 없습니다.")
                continue
            
            for subchapter in subchapters:
                # 차시가 없는 소단원
                chasis = Chasi.objects.filter(sub_chapter=subchapter)
                if not chasis.exists():
                    warnings.append(f"소단원 '{subchapter.sub_chapter_title}'에 차시가 없습니다.")
                    continue
                
                for chasi in chasis:
                    # 슬라이드가 없는 차시
                    slides = ChasiSlide.objects.filter(chasi=chasi)
                    if not slides.exists():
                        warnings.append(f"차시 '{chasi.chasi_title}'에 슬라이드가 없습니다.")
        
        return {'errors': errors, 'warnings': warnings}
        
    except Exception as e:
        errors.append(f"구조 검사 중 오류가 발생했습니다: {str(e)}")
        return {'errors': errors, 'warnings': warnings}


def calculate_course_duration(course):
    """코스의 총 수업 시간을 계산하는 함수"""
    try:
        # 방법 1: 차시별 duration_minutes의 합 - 수정: subchapter -> sub_chapter
        chasi_duration = Chasi.objects.filter(
            sub_chapter__chapter__subject=course  # subchapter를 sub_chapter로 변경
        ).aggregate(
            total_time=Sum('duration_minutes')
        ).get('total_time') or 0
        
        # 방법 2: 슬라이드별 estimated_time의 합 - 수정: subchapter -> sub_chapter
        slide_duration = ChasiSlide.objects.filter(
            chasi__sub_chapter__chapter__subject=course,  # subchapter를 sub_chapter로 변경
            is_active=True
        ).aggregate(
            total_time=Sum('estimated_time')
        ).get('total_time') or 0
        
        return {
            'chasi_based_minutes': chasi_duration,
            'chasi_based_hours': round(chasi_duration / 60, 1) if chasi_duration else 0,
            'slide_based_minutes': slide_duration,
            'slide_based_hours': round(slide_duration / 60, 1) if slide_duration else 0,
            'recommended_minutes': max(chasi_duration, slide_duration),
            'recommended_hours': round(max(chasi_duration, slide_duration) / 60, 1) if max(chasi_duration, slide_duration) else 0,
        }
        
    except Exception as e:
        return {
            'chasi_based_minutes': 0,
            'chasi_based_hours': 0,
            'slide_based_minutes': 0,
            'slide_based_hours': 0,
            'recommended_minutes': 0,
            'recommended_hours': 0,
        }

def calculate_course_duration_0615(course):
    """코스의 총 수업 시간을 계산하는 함수"""
    try:
        # 방법 1: 차시별 duration_minutes의 합
        chasi_duration = Chasi.objects.filter(subject=course).aggregate(
            total_time=Sum('duration_minutes')
        ).get('total_time') or 0
        
        # 방법 2: 슬라이드별 estimated_time의 합
        slide_duration = ChasiSlide.objects.filter(
            chasi__subject=course,
            is_active=True
        ).aggregate(
            total_time=Sum('estimated_time')
        ).get('total_time') or 0
        
        return {
            'chasi_based_minutes': chasi_duration,
            'chasi_based_hours': round(chasi_duration / 60, 1) if chasi_duration else 0,
            'slide_based_minutes': slide_duration,
            'slide_based_hours': round(slide_duration / 60, 1) if slide_duration else 0,
            'recommended_minutes': max(chasi_duration, slide_duration),
            'recommended_hours': round(max(chasi_duration, slide_duration) / 60, 1) if max(chasi_duration, slide_duration) else 0,
        }
        
    except Exception as e:
        return {
            'chasi_based_minutes': 0,
            'chasi_based_hours': 0,
            'slide_based_minutes': 0,
            'slide_based_hours': 0,
            'recommended_minutes': 0,
            'recommended_hours': 0,
        }


from student.models import StudentAnswer

def get_teacher_dashboard_stats(teacher):
    """교사 대시보드 통계 데이터 생성 (수정)"""
    from accounts.models import Student, Class
    from teacher.models import Course, CourseAssignment

    # 교사가 담당하는 학급 및 학생 수
    teacher_classes = Class.objects.filter(teachers=teacher)
    total_students = Student.objects.filter(school_class__in=teacher_classes).distinct().count()
    total_classes_count = teacher_classes.count()
    
    # 전체 코스 및 할당 수
    total_courses = Course.objects.filter(teacher=teacher).count()
    total_assignments = CourseAssignment.objects.filter(course__teacher=teacher).count()
    
    return {
        'total_courses': total_courses,
        'total_students': total_students,
        'total_classes': total_classes_count,
        'total_assignments': total_assignments, # 템플릿과 일치시키기 위해 변수명 변경/추가
    }



def get_teacher_dashboard_stats_060817(teacher):
    """교사 대시보드 통계 데이터 생성"""
    from django.db.models import Count
    from accounts.models import Student, Class # 모델 import 경로 확인 필요
    from teacher.models import Course, CourseAssignment # teacher.models에서 Course, CourseAssignment import
    
    # ★★★ [수정] 교사가 속한 학급의 학생 수를 distinct()로 중복제거하여 카운트 ★★★
    total_students = Student.objects.filter(
        school_class__teachers=teacher
    ).distinct().count()
    
    # ★★★ [수정] 교사가 속한 학급 수를 카운트 ★★★
    total_classes = Class.objects.filter(
        teachers=teacher
    ).count()
    
    # 전체 코스 수
    total_courses = Course.objects.filter(
        teacher=teacher
    ).count()
    
    # 제출 답안 수 (최근 일주일 등 기준 추가 가능)
    recent_submissions = StudentAnswer.objects.filter(
        slide__chasi__subject__teacher=teacher
    ).count()
    
    return {
        'total_students': total_students,
        'total_classes': total_classes,
        'total_courses': total_courses,
        'recent_submissions': recent_submissions,
    }


def get_teacher_dashboard_stats_0608(teacher):
    """교사 대시보드 통계 데이터 생성"""
    from django.db.models import Count, Q
    from django.utils import timezone
    
    # 전체 학생 수
    total_students = Student.objects.filter(
        school_class__teachers=teacher
    ).count()
    
    # 전체 학급 수
    total_classes = Class.objects.filter(
        teacher=teacher
    ).count()
    
    # 전체 코스 수
    total_courses = Course.objects.filter(
        teacher=teacher
    ).count()
    
    # 활성 할당 수 (완료되지 않은 할당)
    active_assignments = CourseAssignment.objects.filter(
        course__teacher=teacher,
        is_completed=False
    ).count()
    
    # 이번 주 생성된 코스 수
    week_start = timezone.now() - timezone.timedelta(days=7)
    courses_this_week = Course.objects.filter(
        teacher=teacher,
        created_at__gte=week_start
    ).count()
    
    # 마감일이 임박한 할당 (3일 이내)
    upcoming_due = CourseAssignment.objects.filter(
        course__teacher=teacher,
        is_completed=False,
        due_date__isnull=False,
        due_date__lte=timezone.now() + timezone.timedelta(days=3),
        due_date__gte=timezone.now()
    ).count()
    
    return {
        'total_students': total_students,
        'total_classes': total_classes,
        'total_courses': total_courses,
        'active_assignments': active_assignments,
        'courses_this_week': courses_this_week,
        'upcoming_due': upcoming_due,
    }

def get_teacher_dashboard_stats_0603(teacher):

    """교사 대시보드용 통계를 반환하는 함수"""
    try:
        from accounts.models import Student, Class
        
        stats = {
            # 기본 통계
            'total_courses': Course.objects.filter(teacher=teacher).count(),
            'total_chapters': Chapter.objects.filter(subject__teacher=teacher).count(),
            'total_subchapters': SubChapter.objects.filter(subject__teacher=teacher).count(),
            'total_chasis': Chasi.objects.filter(subject__teacher=teacher).count(),
            'total_slides': ChasiSlide.objects.filter(chasi__subject__teacher=teacher).count(),
            'total_classes': Class.objects.filter(teacher=teacher).count(),
            'total_students': Student.objects.filter(school_class__teachers=teacher).count(),
            
            # 컨텐츠 통계
            'published_chasis': Chasi.objects.filter(
                subject__teacher=teacher,
                is_published=True
            ).count(),
            'active_slides': ChasiSlide.objects.filter(
                chasi__subject__teacher=teacher,
                is_active=True
            ).count(),
            
            # 할당 통계
            'total_assignments': Course.objects.filter(teacher=teacher).aggregate(
                total=Count('courseassignment')
            ).get('total') or 0,
        }
        
        # 진행률 계산
        if stats['total_chasis'] > 0:
            stats['completion_rate'] = round(
                (stats['published_chasis'] / stats['total_chasis']) * 100, 1
            )
        else:
            stats['completion_rate'] = 0
        
        return stats
        
    except Exception as e:
        # 기본값 반환
        return {
            'total_courses': 0,
            'total_chapters': 0,
            'total_subchapters': 0,
            'total_chasis': 0,
            'total_slides': 0,
            'total_classes': 0,
            'total_students': 0,
            'published_chasis': 0,
            'active_slides': 0,
            'total_assignments': 0,
            'completion_rate': 0,
        }
    

def generate_content_html(content_type, data):
    """콘텐츠 타입에 따른 HTML 생성"""
    templates = {
        '객관식 문제': 'teacher/contents/templates/multiple_choice.html',
        '단답형 문제': 'teacher/contents/templates/short_answer.html',
        '서술형 문제': 'teacher/contents/templates/essay.html',
        '논술형 문제': 'teacher/contents/templates/long_essay.html',
        'PPT': 'teacher/contents/templates/presentation.html',
        '리포트': 'teacher/contents/templates/report.html',
        '기록 제출폼': 'teacher/contents/templates/submission_form.html',
    }
    
    template_name = templates.get(content_type.type_name, 'teacher/contents/templates/default.html')
    
    try:
        html = render_to_string(template_name, data)
        return html
    except:
        return data.get('content', '')
    
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import json
def validate_json_field(value):
    """JSON 필드 유효성 검사"""
    if isinstance(value, str):
        try:
            json.loads(value)
            return True, None
        except json.JSONDecodeError as e:
            return False, str(e)
    elif isinstance(value, dict):
        return True, None
    else:
        return False, "Invalid JSON format"

def calculate_slide_duration(slides):
    """슬라이드들의 총 예상 시간 계산"""
    return sum(slide.estimated_time for slide in slides)

def reorder_slides(chasi):
    """차시의 슬라이드 번호 재정렬"""
    slides = ChasiSlide.objects.filter(chasi=chasi).order_by('slide_number')
    for idx, slide in enumerate(slides, 1):
        if slide.slide_number != idx:
            slide.slide_number = idx
            slide.save(update_fields=['slide_number'])
