from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg, Prefetch, F
from django.utils import timezone
from django.http import JsonResponse
from functools import wraps
from decimal import Decimal
from django.db import transaction
from django.views.decorators.http import require_POST

from accounts.models import Student
from teacher.models import (
    Course, CourseAssignment, Chapter, SubChapter, 
    Chasi, ChasiSlide, Contents, ContentType
)
from .models import StudentProgress, StudentAnswer, StudentNote
from datetime import datetime, timedelta
from .utils import *
from django.db import transaction # 트랜잭션 처리를 위해 추가



def student_required(view_func):
    """학생 권한 필요한 뷰 데코레이터"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, '로그인이 필요합니다.')
            return redirect('accounts:login')
        
        if not hasattr(request.user, 'student'):
            messages.error(request, '학생만 접근 가능합니다.')
            return redirect('accounts:login')
        
        return view_func(request, *args, **kwargs)
    
    return login_required(_wrapped_view)


@login_required
@student_required
def learning_course_view_0604(request, course_id):
    """코스 학습 페이지"""
    try:
        student = request.user.student
        course = get_object_or_404(Course, id=course_id)
        
        # 권한 확인
        has_permission = CourseAssignment.objects.filter(
            course=course,
        ).filter(
            Q(assigned_class=student.school_class) | Q(assigned_student=student)
        ).exists()
        
        if not has_permission:
            messages.error(request, '해당 코스에 접근 권한이 없습니다.')
            return redirect('student:course_list')
        
        # 대단원별로 차시와 슬라이드 가져오기
        chapters = Chapter.objects.filter(
            subject=course
        ).prefetch_related(
            Prefetch('subchapters',
                queryset=SubChapter.objects.filter(
                    subject=course
                ).prefetch_related(
                    Prefetch('chasis',
                        queryset=Chasi.objects.filter(
                            subject=course,
                            is_published=True
                        ).prefetch_related(
                            Prefetch('teacher_slides',
                                queryset=ChasiSlide.objects.all().select_related('content_type', 'content')
                            )
                        )
                    )
                )
            )
        ).order_by('chapter_order')
        
        # 진도 정보를 딕셔너리로 변환
        progress_list = StudentProgress.objects.filter(
            student=student,
            slide__chasi__sub_chapter__chapter__subject=course
        ).select_related('slide')
        
        # 진도 정보를 처리하여 템플릿에서 사용하기 쉽게 만들기
        progress_data = {}
        for progress in progress_list:
            progress_data[progress.slide.id] = {
                'is_completed': progress.is_completed,
                'started_at': progress.started_at,
                'view_count': progress.view_count if hasattr(progress, 'view_count') else 0
            }
        
        # 전체 진도율 계산
        total_slides = ChasiSlide.objects.filter(
            chasi__sub_chapter__chapter__subject=course
        ).count()
        
        completed_slides = progress_list.filter(is_completed=True).count()
        
        if total_slides > 0:
            overall_progress = int((completed_slides / total_slides) * 100)
        else:
            overall_progress = 0
        
        context = {
            'course': course,
            'chapters': chapters,
            'progress_data': progress_data,
            'overall_progress': overall_progress,
            'total_slides': total_slides,
            'completed_slides': completed_slides,
        }
        
        return render(request, 'student/learning_course.html', context)
        
    except Exception as e:
        messages.error(request, f'오류가 발생했습니다: {str(e)}')
        return redirect('student:course_list')



@login_required
def slide_view_0606(request, slide_id):
    """슬라이드 뷰 - 기존 함수에 existing_answer 추가"""
    # 사용자 인증 확인
    if not request.user.is_authenticated:
        messages.error(request, '로그인이 필요합니다.')
        return redirect('account:login')
    
    slide = get_object_or_404(ChasiSlide, id=slide_id)
    
    # 학생 객체 가져오기
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, '학생 계정을 찾을 수 없습니다.')
        # 학생 계정이 없는 경우 적절한 페이지로 리다이렉트
        # 'student:course_list'가 없다면 다른 적절한 URL로 변경
        try:
            return redirect('student:course_list')
        except:
            # course_list URL이 없는 경우 홈페이지나 다른 기본 페이지로
            return redirect('/')  # 또는 적절한 기본 URL
    
    # 기존 답안 확인
    existing_answer = None
    if slide.content_type.type_name in ['객관식', '단답형', '선택형']:
        try:
            existing_answer = StudentAnswer.objects.filter(
                student=student,
                slide=slide
            ).latest('submitted_at')
        except StudentAnswer.DoesNotExist:
            pass
    
    # 이전/다음 슬라이드 찾기
    prev_slide = ChasiSlide.objects.filter(
        chasi=slide.chasi,
        slide_number__lt=slide.slide_number
    ).order_by('-slide_number').first()
    
    next_slide = ChasiSlide.objects.filter(
        chasi=slide.chasi,
        slide_number__gt=slide.slide_number
    ).order_by('slide_number').first()
    
    # 진도 데이터 (기존 로직)
    progress_data = {}  # 실제 진도 데이터 로직은 기존 코드 사용
    
    # 노트 가져오기 (기존 로직)
    note = None  # 실제 노트 로직은 기존 코드 사용
    
    context = {
        'slide': slide,
        'prev_slide': prev_slide,
        'next_slide': next_slide,
        'progress_data': progress_data,
        'note': note,
        'existing_answer': existing_answer,  # 추가
    }
    
    return render(request, 'student/slide_view.html', context)



@login_required
def slide_view_0605(request, slide_id):
    """슬라이드 뷰 - 기존 함수에 existing_answer 추가"""
    # 사용자 인증 확인
    if not request.user.is_authenticated:
        messages.error(request, '로그인이 필요합니다.')
        return redirect('account:login')
    
    slide = get_object_or_404(ChasiSlide, id=slide_id)
    
    # 학생 객체 가져오기
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, '학생 계정을 찾을 수 없습니다.')
        # 학생 계정이 없는 경우 적절한 페이지로 리다이렉트
        # 'student:course_list'가 없다면 다른 적절한 URL로 변경
        try:
            return redirect('student:course_list')
        except:
            # course_list URL이 없는 경우 홈페이지나 다른 기본 페이지로
            return redirect('/')  # 또는 적절한 기본 URL
    
    # 기존 답안 확인
    existing_answer = None
    if slide.content_type.type_name in ['객관식', '단답형', '선택형']:
        try:
            existing_answer = StudentAnswer.objects.filter(
                student=student,
                slide=slide
            ).latest('submitted_at')
        except StudentAnswer.DoesNotExist:
            pass
    
    # 이전/다음 슬라이드 찾기
    prev_slide = ChasiSlide.objects.filter(
        chasi=slide.chasi,
        slide_number__lt=slide.slide_number
    ).order_by('-slide_number').first()
    
    next_slide = ChasiSlide.objects.filter(
        chasi=slide.chasi,
        slide_number__gt=slide.slide_number
    ).order_by('slide_number').first()
    
    # 진도 데이터 (기존 로직)
    progress_data = {}  # 실제 진도 데이터 로직은 기존 코드 사용
    
    # 노트 가져오기 (기존 로직)
    note = None  # 실제 노트 로직은 기존 코드 사용
    
    context = {
        'slide': slide,
        'prev_slide': prev_slide,
        'next_slide': next_slide,
        'progress_data': progress_data,
        'note': note,
        'existing_answer': existing_answer,  # 추가
    }
    
    return render(request, 'student/slide_view.html', context)


@login_required
@require_POST
def check_answer_060619(request):
    """답안 체크 및 저장을 처리하는 AJAX 뷰 (리팩토링 버전)"""
    try:
        # 1. 데이터 가져오기 및 검증
        content_id = request.POST.get('content_id')
        student_answer_str = request.POST.get('student_answer', '').strip()
        slide_id = request.POST.get('slide_id')

        if not all([content_id, student_answer_str, slide_id]):
            return JsonResponse({
                'status': 'error',
                'message': '필수 데이터가 누락되었습니다.',
                'jungoh': 'error'
            }, status=400)

        # 2. 객체 조회
        try:
            student = request.user.student
            slide = ChasiSlide.objects.select_related('content').get(id=slide_id)
            
            # 슬라이드에 연결된 콘텐츠 ID와 요청으로 받은 콘텐츠 ID가 일치하는지 확인
            if str(slide.content.id) != content_id:
                return JsonResponse({
                    'status': 'error',
                    'message': '슬라이드와 콘텐츠 정보가 일치하지 않습니다.',
                    'jungoh': 'error'
                }, status=400)
            content = slide.content
        except (Student.DoesNotExist, ChasiSlide.DoesNotExist) as e:
            return JsonResponse({
                'status': 'error',
                'message': f'필요한 데이터를 찾을 수 없습니다: {str(e)}',
                'jungoh': 'error'
            }, status=404)

        # 3. 정답 비교
        correct_answer = parse_correct_answer(content.answer)
        is_correct = (student_answer_str == correct_answer)
        score = 100.0 if is_correct else 0.0
        
        answer_data = {
            'selected_answer': student_answer_str,
            'correct_answer': correct_answer,
            # 'answer_type' 등 필요한 메타정보 추가 가능
        }

        # 4. update_or_create로 답안 생성 또는 업데이트 (핵심 변경사항)
        student_answer_obj, created = StudentAnswer.objects.update_or_create(
            student=student,
            slide=slide,
            defaults={
                'answer': answer_data,
                'is_correct': is_correct,
                'score': score,
                'feedback': '자동 채점 완료',
            }
        )

        print(f"답안 {'생성' if created else '업데이트'} 완료: ID {student_answer_obj.id} (학생: {student.id}, 슬라이드: {slide.id})")

        # 5. 성공 응답 반환
        response_data = {
            'status': 'success',
            'jungoh': 'right' if is_correct else 'wrong',
            'is_correct': is_correct,
            'correct_answer': correct_answer,
            'student_answer': student_answer_str,
            'score': student_answer_obj.score,
            'submitted_at': student_answer_obj.submitted_at.strftime('%Y-%m-%d %H:%M:%S'),
            'feedback': student_answer_obj.feedback,
            'is_first_submit': created
        }
        return JsonResponse(response_data)

    except Exception as e:
        import traceback
        print(f"ERROR: check_answer 뷰에서 예외 발생: {str(e)}")
        print(f"트레이스백: {traceback.format_exc()}")
        return JsonResponse({
            'status': 'error',
            'message': f'서버 오류가 발생했습니다: {str(e)}',
            'jungoh': 'error'
        }, status=500)

@login_required
@require_POST
def check_answer_060613(request):
    """답안 체크 AJAX 뷰 - utils.py 함수를 정밀하게 활용"""
    print("=== 답안 체크 시작 ===")
    print(f"사용자: {request.user}")
    print(f"요청 데이터: {request.POST}")

    try:
        # 요청 데이터 가져오기
        content_id = request.POST.get('content_id')
        student_answer = request.POST.get('student_answer')
        slide_id = request.POST.get('slide_id')
        is_resubmit = request.POST.get('is_resubmit', 'false').lower() == 'true'

        print(f"content_id: {content_id}, student_answer: {student_answer}, "
              f"slide_id: {slide_id}, is_resubmit:{is_resubmit}")

        # 필수 데이터 검증
        if not all([content_id, student_answer, slide_id]):
            return JsonResponse({
                'status': 'error',
                'message': '필수 데이터가 누락되었습니다.',
                'jungoh': 'error'
            })

        # 객체 조회
        print("=== 객체 조회 시작 ===")
        try:
            student = Student.objects.get(user=request.user)
            slide = ChasiSlide.objects.get(id=slide_id)
            content = Contents.objects.get(id=content_id)
            
            print(f"Student: {student.id}, ChasiSlide: {slide.id}, Contents: {content.id}")
        except (Student.DoesNotExist, ChasiSlide.DoesNotExist, Contents.DoesNotExist) as e:
            print(f"객체 조회 실패: {e}")
            return JsonResponse({
                'status': 'error',
                'message': f'필요한 데이터를 찾을 수 없습니다: {str(e)}',
                'jungoh': 'error'
            })

        # 정답 파싱
        print("=== 정답 비교 시작 ===")
        correct_answer = parse_correct_answer(content.answer)
        student_answer_clean = student_answer.strip()

        print(f"파싱된 정답: '{correct_answer}', 학생 답안: '{student_answer_clean}'")

        # 정답 여부 판단 (간단 비교)
        is_correct = (student_answer_clean == correct_answer)
        print(f"정답 여부: {is_correct}")

        # 기존 답안 확인
        existing_answer = StudentAnswer.objects.filter(
            student=student,
            slide=slide
        ).order_by('-submitted_at').first()

        print("=== 데이터베이스 저장 시작 ===")

       # views.py (혹은 student/views.py)

        if is_resubmit:
            if existing_answer:
                # 재제출 -> 기존 답안 업데이트
                student_answer_obj = update_existing_answer(
                    existing_answer,
                    student_answer_clean,
                    correct_answer,
                    is_correct
                )
            else:
                # 재제출이지만 기존 답안이 없으면 새로 생성(이 경우도 ORM만 사용)
                student_answer_obj = create_new_answer(
                    student, slide, student_answer_clean, correct_answer, is_correct
                )
        else:
            # 최초 제출 -> 새 답안 생성
            student_answer_obj = create_new_answer(
                student, slide, student_answer_clean, correct_answer, is_correct
            )


        # 생성/업데이트 성공 여부 확인
        if not student_answer_obj:
            return JsonResponse({
                'status': 'error',
                'message': '답안 저장에 실패했습니다.',
                'jungoh': 'error'
            })

        print(f"답안 처리 완료: {student_answer_obj.id}")

        # 응답 데이터 구성
        response_data = {
            'status': 'success',
            'jungoh': 'right' if is_correct else 'wrong',
            'is_correct': is_correct,
            'correct_answer': correct_answer,
            'student_answer': student_answer_clean,
            'score': student_answer_obj.score,
            'submitted_at': student_answer_obj.submitted_at.strftime('%Y-%m-%d %H:%M:%S'),
            'feedback': student_answer_obj.feedback
        }

        print(f"응답 데이터: {response_data}")
        return JsonResponse(response_data)

    except Exception as e:
        print(f"ERROR: 전체 예외 발생: {str(e)}")
        import traceback
        print(f"트레이스백: {traceback.format_exc()}")

        return JsonResponse({
            'status': 'error',
            'message': f'서버 오류가 발생했습니다: {str(e)}',
            'jungoh': 'error'
        })

# student/views.py
@login_required
@require_POST
def check_answer_0606_12(request):
    """답안 체크 AJAX 뷰 - 간단 버전"""
    print("=== 답안 체크 시작 ===")
    print(f"사용자: {request.user}")
    print(f"요청 데이터: {request.POST}")
    
    try:
        # 요청 데이터 가져오기
        content_id = request.POST.get('content_id')
        student_answer = request.POST.get('student_answer')
        slide_id = request.POST.get('slide_id')
        is_resubmit = request.POST.get('is_resubmit', 'false').lower() == 'true'
        
        print(f"content_id: {content_id}, student_answer: {student_answer}, slide_id: {slide_id},is_resubmit:{is_resubmit}")
        
        # 필수 데이터 검증
        if not all([content_id, student_answer, slide_id]):
            return JsonResponse({
                'status': 'error',
                'message': '필수 데이터가 누락되었습니다.',
                'jungoh': 'error'
            })
        
        # 객체 조회
        print("=== 객체 조회 시작 ===")
        
        try:
            student = Student.objects.get(user=request.user)
            slide = ChasiSlide.objects.get(id=slide_id)
            content = Contents.objects.get(id=content_id)
            print(f"Student: {student.id}, ChasiSlide: {slide.id}, Contents: {content.id}")
        except (Student.DoesNotExist, ChasiSlide.DoesNotExist, Contents.DoesNotExist) as e:
            print(f"객체 조회 실패: {e}")
            return JsonResponse({
                'status': 'error',
                'message': f'필요한 데이터를 찾을 수 없습니다: {str(e)}',
                'jungoh': 'error'
            })
        
        # 정답 파싱 (JSON 처리)
        print("=== 정답 비교 시작 ===")
        correct_answer = parse_correct_answer(content.answer)
        student_answer_clean = student_answer.strip()
        
        print(f"파싱된 정답: '{correct_answer}', 학생 답안: '{student_answer_clean}'")
        
        # 정답 여부 판단
        is_correct = (student_answer_clean == correct_answer)
        print(f"정답 여부: {is_correct}")
        
        # 기존 답안 확인
        existing_answer = StudentAnswer.objects.filter(
            student=student,
            slide=slide
        ).first()
        
        # StudentAnswer 저장
        print("=== 데이터베이스 저장 시작 ===")
        
        if is_resubmit and existing_answer:
            # 기존 답안 업데이트
            print("기존 답안 업데이트 중...")
            student_answer_obj = update_existing_answer(
                existing_answer, student_answer_clean, correct_answer, is_correct
            )
        else:
            # 새 답안 생성
            print("새 답안 생성 중...")
            student_answer_obj = create_new_answer(
                student, slide, student_answer_clean, correct_answer, is_correct
            )
        
        if not student_answer_obj:
            return JsonResponse({
                'status': 'error',
                'message': '답안 저장에 실패했습니다.',
                'jungoh': 'error'
            })
        
        print(f"답안 저장 완료: {student_answer_obj.id}")
        
        # 응답 데이터 구성
        response_data = {
            'status': 'success',
            'jungoh': 'right' if is_correct else 'wrong',
            'is_correct': is_correct,
            'correct_answer': correct_answer,
            'student_answer': student_answer_clean,
            'score': student_answer_obj.score,
            'submitted_at': student_answer_obj.submitted_at.strftime('%Y-%m-%d %H:%M:%S'),
            'feedback': student_answer_obj.feedback
        }
        
        print(f"응답 데이터: {response_data}")
        return JsonResponse(response_data)
        
    except Exception as e:
        print(f"ERROR: 전체 예외 발생: {str(e)}")
        import traceback
        print(f"트레이스백: {traceback.format_exc()}")
        
        return JsonResponse({
            'status': 'error',
            'message': f'서버 오류가 발생했습니다: {str(e)}',
            'jungoh': 'error'
        })

@login_required
@require_POST  
def check_answer_0606_complex(request):
    """답안 체크 AJAX 뷰"""
    print("=== 답안 체크 시작 ===")
    print(f"사용자: {request.user}")
    print(f"사용자 인증 상태: {request.user.is_authenticated}")
    print(f"요청 데이터: {request.POST}")
    
    try:
        # 사용자 인증 확인
        if not request.user.is_authenticated:
            print("ERROR: 사용자가 인증되지 않음")
            return JsonResponse({
                'status': 'error',
                'message': '로그인이 필요합니다.',
                'jungoh': 'error'
            })
        
        # 요청 데이터 가져오기
        content_id = request.POST.get('content_id')
        student_answer = request.POST.get('student_answer')
        slide_id = request.POST.get('slide_id')
        is_resubmit = request.POST.get('is_resubmit', 'false').lower() == 'true'
        
        print(f"content_id: {content_id}")
        print(f"student_answer: {student_answer}")
        print(f"slide_id: {slide_id}")
        print(f"is_resubmit: {is_resubmit}")
        
        # 필수 데이터 검증
        if not all([content_id, student_answer, slide_id]):
            print("ERROR: 필수 데이터 누락")
            return JsonResponse({
                'status': 'error',
                'message': '필수 데이터가 누락되었습니다.',
                'jungoh': 'error'
            })
        
        # 객체 가져오기
        print("=== 객체 조회 시작 ===")
        
        # Student 객체 조회
        try:
            print(f"Student 조회 시도: user={request.user.id}")
            student = Student.objects.get(user=request.user)
            print(f"Student 조회 성공: {student.id} - {student}")
        except Student.DoesNotExist:
            print("ERROR: Student 객체를 찾을 수 없음")
            return JsonResponse({
                'status': 'error',
                'message': '학생 계정을 찾을 수 없습니다. 관리자에게 문의하세요.',
                'jungoh': 'error'
            })
        
        # ChasiSlide 객체 조회
        try:
            print(f"ChasiSlide 조회 시도: id={slide_id}")
            slide = ChasiSlide.objects.get(id=slide_id)
            print(f"ChasiSlide 조회 성공: {slide.id} - {slide}")
        except ChasiSlide.DoesNotExist:
            print("ERROR: ChasiSlide 객체를 찾을 수 없음")
            return JsonResponse({
                'status': 'error',
                'message': f'슬라이드를 찾을 수 없습니다. (ID: {slide_id})',
                'jungoh': 'error'
            })
        
        # Contents 객체 조회
        try:
            print(f"Contents 조회 시도: id={content_id}")
            content = Contents.objects.get(id=content_id)
            print(f"Contents 조회 성공: {content.id} - {content}")
            print(f"Contents 정답 원본: {content.answer}")
        except Contents.DoesNotExist:
            print("ERROR: Contents 객체를 찾을 수 없음")
            return JsonResponse({
                'status': 'error',
                'message': f'콘텐츠를 찾을 수 없습니다. (ID: {content_id})',
                'jungoh': 'error'
            })
        
        print("=== 객체 조회 완료 ===")
        
        # 정답 비교 - JSON 파싱 처리
        print("=== 정답 비교 시작 ===")
        
        # Contents의 answer 필드 파싱
        correct_answer = None
        try:
            if content.answer:
                # JSON 형태인지 확인
                if content.answer.strip().startswith('{'):
                    import json
                    answer_data = json.loads(content.answer)
                    correct_answer = str(answer_data.get('answer', ''))
                    print(f"JSON에서 파싱된 정답: '{correct_answer}'")
                else:
                    correct_answer = content.answer.strip()
                    print(f"일반 텍스트 정답: '{correct_answer}'")
            else:
                correct_answer = ''
                print("정답이 비어있음")
        except json.JSONDecodeError:
            print("JSON 파싱 실패 - 일반 텍스트로 처리")
            correct_answer = content.answer.strip() if content.answer else ''
        except Exception as e:
            print(f"정답 파싱 중 오류: {str(e)}")
            correct_answer = content.answer.strip() if content.answer else ''
        
        student_answer_clean = student_answer.strip()
        
        print(f"파싱된 정답: '{correct_answer}'")
        print(f"학생 답안: '{student_answer_clean}'")
        print(f"문제 유형: {content.content_type.type_name}")
        
        # 정답 여부 판단
        is_correct = False
        if content.content_type.type_name in ['객관식', '선택형', 'multiple-choice']:
            # 객관식: 정확히 일치
            is_correct = student_answer_clean == correct_answer
            print(f"객관식 비교 결과: {is_correct}")
        elif content.content_type.type_name == '단답형':
            # 단답형: 대소문자 구분없이 비교
            is_correct = student_answer_clean.lower() == correct_answer.lower()
            print(f"단답형 비교 결과: {is_correct}")
        
        print(f"최종 정답 여부: {is_correct}")
        print("=== 정답 비교 완료 ===")
        
        # 답안 데이터 구성
        answer_data = {
            'selected_answer': student_answer_clean,
            'correct_answer': correct_answer,
            'answer_type': content.content_type.type_name,
            'submitted_at': timezone.now().isoformat()
        }
        print(f"답안 데이터: {answer_data}")
        
        # 데이터베이스에 저장/업데이트
        print("=== 데이터베이스 저장 시작 ===")
        
        # 기존 답안 확인
        existing_answer = StudentAnswer.objects.filter(
            student=student,
            slide=slide
        ).first()
        
        if existing_answer:
            print(f"기존 답안 발견: {existing_answer.id}")
        else:
            print("기존 답안 없음")
        
        # StudentAnswer 생성/수정 (트랜잭션 없이 직접 처리)
        try:
            if is_resubmit and existing_answer:
                # 재제출: 기존 답안 업데이트
                print("기존 답안 업데이트 중...")
                existing_answer.answer = answer_data
                existing_answer.is_correct = is_correct
                existing_answer.score = 100.0 if is_correct else 0.0
                existing_answer.submitted_at = timezone.now()
                existing_answer.feedback = '자동 채점 결과'
                existing_answer.save()
                student_answer_obj = existing_answer
                print(f"기존 답안 업데이트 완료: {student_answer_obj.id}")
            else:
                # 새 답안 생성
                print("새 답안 생성 중...")
                print(f"생성할 데이터 - student: {student.id}, slide: {slide.id}")
                
                # 필수 필드만 사용하여 생성
                student_answer_obj = StudentAnswer(
                    student=student,
                    slide=slide,
                    answer=answer_data,
                    is_correct=is_correct,
                    score=100.0 if is_correct else 0.0,
                    feedback='자동 채점 결과'
                )
                
                # 저장하기 전 유효성 검사
                try:
                    student_answer_obj.full_clean()
                    print("모델 유효성 검사 통과")
                except Exception as validation_error:
                    print(f"모델 유효성 검사 실패: {validation_error}")
                    raise validation_error
                
                student_answer_obj.save()
                print(f"새 답안 생성 완료: {student_answer_obj.id}")
                
        except Exception as e:
            print(f"ERROR: 데이터베이스 저장 중 오류 발생: {str(e)}")
            print(f"오류 타입: {type(e)}")
            
            # 더 자세한 에러 정보
            import traceback
            print(f"트레이스백: {traceback.format_exc()}")
            
            return JsonResponse({
                'status': 'error',
                'message': f'답안 저장 중 오류가 발생했습니다: {str(e)}',
                'jungoh': 'error'
            })
        
        print("=== 데이터베이스 저장 완료 ===")
        
        # 응답 데이터 구성
        response_data = {
            'status': 'success',
            'jungoh': 'right' if is_correct else 'wrong',
            'is_correct': is_correct,
            'correct_answer': correct_answer,
            'student_answer': student_answer_clean,
            'score': student_answer_obj.score,
            'submitted_at': student_answer_obj.submitted_at.strftime('%Y-%m-%d %H:%M:%S'),
            'feedback': student_answer_obj.feedback
        }
        
        print(f"응답 데이터: {response_data}")
        print("=== 답안 체크 완료 ===")
        
        return JsonResponse(response_data)
        
    except Exception as e:
        # 예외 처리
        print(f"ERROR: 전체 예외 발생: {str(e)}")
        print(f"예외 타입: {type(e)}")
        
        # 더 자세한 에러 정보
        import traceback
        print(f"전체 트레이스백: {traceback.format_exc()}")
        
        return JsonResponse({
            'status': 'error',
            'message': f'서버 오류가 발생했습니다: {str(e)}',
            'jungoh': 'error'
        })



@login_required
@require_POST
def check_answer_0606(request):
    """답안 체크 AJAX 뷰"""
    print("=== 답안 체크 시작 ===")
    print(f"사용자: {request.user}")
    print(f"사용자 인증 상태: {request.user.is_authenticated}")
    print(f"요청 데이터: {request.POST}")
    
    try:
        # 사용자 인증 확인
        if not request.user.is_authenticated:
            print("ERROR: 사용자가 인증되지 않음")
            return JsonResponse({
                'status': 'error',
                'message': '로그인이 필요합니다.',
                'jungoh': 'error'
            })
        
        # 요청 데이터 가져오기
        content_id = request.POST.get('content_id')
        student_answer = request.POST.get('student_answer')
        slide_id = request.POST.get('slide_id')
        is_resubmit = request.POST.get('is_resubmit', 'false').lower() == 'true'
        
        print(f"content_id: {content_id}")
        print(f"student_answer: {student_answer}")
        print(f"slide_id: {slide_id}")
        print(f"is_resubmit: {is_resubmit}")
        
        # 필수 데이터 검증
        if not all([content_id, student_answer, slide_id]):
            print("ERROR: 필수 데이터 누락")
            print(f"content_id 존재: {bool(content_id)}")
            print(f"student_answer 존재: {bool(student_answer)}")
            print(f"slide_id 존재: {bool(slide_id)}")
            return JsonResponse({
                'status': 'error',
                'message': '필수 데이터가 누락되었습니다.',
                'jungoh': 'error'
            })
        
        # 객체 가져오기
        print("=== 객체 조회 시작 ===")
        
        # Student 객체 조회
        try:
            print(f"Student 조회 시도: user={request.user.id}")
            student = Student.objects.get(user=request.user)
            print(f"Student 조회 성공: {student.id} - {student}")
        except Student.DoesNotExist:
            print("ERROR: Student 객체를 찾을 수 없음")
            print(f"현재 사용자: {request.user}")
            print(f"사용자 ID: {request.user.id}")
            # Student 객체가 없는 경우 생성하거나 오류 처리
            return JsonResponse({
                'status': 'error',
                'message': '학생 계정을 찾을 수 없습니다. 관리자에게 문의하세요.',
                'jungoh': 'error'
            })
        except Exception as e:
            print(f"ERROR: Student 조회 중 예외 발생: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'학생 계정 조회 오류: {str(e)}',
                'jungoh': 'error'
            })
        
        # ChasiSlide 객체 조회
        try:
            print(f"ChasiSlide 조회 시도: id={slide_id}")
            slide = ChasiSlide.objects.get(id=slide_id)
            print(f"ChasiSlide 조회 성공: {slide.id} - {slide}")
        except ChasiSlide.DoesNotExist:
            print("ERROR: ChasiSlide 객체를 찾을 수 없음")
            return JsonResponse({
                'status': 'error',
                'message': f'슬라이드를 찾을 수 없습니다. (ID: {slide_id})',
                'jungoh': 'error'
            })
        except Exception as e:
            print(f"ERROR: ChasiSlide 조회 중 예외 발생: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'슬라이드 조회 오류: {str(e)}',
                'jungoh': 'error'
            })
        
        # Contents 객체 조회
        try:
            print(f"Contents 조회 시도: id={content_id}")
            content = Contents.objects.get(id=content_id)
            print(f"Contents 조회 성공: {content.id} - {content}")
            print(f"Contents 정답: {content.answer}")
        except Contents.DoesNotExist:
            print("ERROR: Contents 객체를 찾을 수 없음")
            return JsonResponse({
                'status': 'error',
                'message': f'콘텐츠를 찾을 수 없습니다. (ID: {content_id})',
                'jungoh': 'error'
            })
        except Exception as e:
            print(f"ERROR: Contents 조회 중 예외 발생: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'콘텐츠 조회 오류: {str(e)}',
                'jungoh': 'error'
            })
        
        print("=== 객체 조회 완료 ===")
        
        # 정답 비교
        print("=== 정답 비교 시작 ===")
        correct_answer = content.answer.strip() if content.answer else ''
        student_answer_clean = student_answer.strip()
        
        print(f"정답: '{correct_answer}'")
        print(f"학생 답안: '{student_answer_clean}'")
        print(f"문제 유형: {content.content_type.type_name}")
        
        # 정답 여부 판단
        is_correct = False
        if content.content_type.type_name in ['객관식', '선택형']:
            # 객관식: 정확히 일치
            is_correct = student_answer_clean == correct_answer
            print(f"객관식 비교 결과: {is_correct}")
        elif content.content_type.type_name == '단답형':
            # 단답형: 대소문자 구분없이 비교
            is_correct = student_answer_clean.lower() == correct_answer.lower()
            print(f"단답형 비교 결과: {is_correct}")
        
        print(f"최종 정답 여부: {is_correct}")
        print("=== 정답 비교 완료 ===")
        
        # 답안 데이터 구성
        answer_data = {
            'selected_answer': student_answer_clean,
            'correct_answer': correct_answer,
            'answer_type': content.content_type.type_name,
            'submitted_at': timezone.now().isoformat()
        }
        print(f"답안 데이터: {answer_data}")
        
        # 데이터베이스에 저장/업데이트
        print("=== 데이터베이스 저장 시작 ===")
        
        # 기존 답안 확인
        existing_answer = None
        try:
            existing_answer = StudentAnswer.objects.filter(
                student=student,
                slide=slide
            ).first()
            
            if existing_answer:
                print(f"기존 답안 발견: {existing_answer.id}")
            else:
                print("기존 답안 없음")
        except Exception as e:
            print(f"기존 답안 조회 중 오류: {str(e)}")
        
        try:
            with transaction.atomic():
                if is_resubmit and existing_answer:
                    # 재제출: 기존 답안 업데이트
                    print("기존 답안 업데이트 중...")
                    existing_answer.answer = answer_data
                    existing_answer.is_correct = is_correct
                    existing_answer.score = 100.0 if is_correct else 0.0
                    existing_answer.submitted_at = timezone.now()
                    existing_answer.feedback = '자동 채점 결과'
                    existing_answer.save()
                    student_answer_obj = existing_answer
                    print(f"기존 답안 업데이트 완료: {student_answer_obj.id}")
                else:
                    # 첫 제출 또는 기존 답안이 없는 경우: 새 답안 생성
                    print("새 답안 생성 중...")
                    print(f"생성할 데이터 - student: {student.id}, slide: {slide.id}")
                    
                    student_answer_obj = StudentAnswer.objects.create(
                        student=student,
                        slide=slide,
                        answer=answer_data,
                        is_correct=is_correct,
                        score=100.0 if is_correct else 0.0,
                        feedback='자동 채점 결과'
                    )
                    print(f"새 답안 생성 완료: {student_answer_obj.id}")
                    
        except Exception as e:
            print(f"ERROR: 데이터베이스 저장 중 오류 발생: {str(e)}")
            print(f"오류 타입: {type(e)}")
            
            # 더 자세한 에러 정보
            import traceback
            print(f"트레이스백: {traceback.format_exc()}")
            
            return JsonResponse({
                'status': 'error',
                'message': f'답안 저장 중 오류가 발생했습니다: {str(e)}',
                'jungoh': 'error'
            })
        
        print("=== 데이터베이스 저장 완료 ===")
        
        # 응답 데이터 구성
        response_data = {
            'status': 'success',
            'jungoh': 'right' if is_correct else 'wrong',
            'is_correct': is_correct,
            'correct_answer': correct_answer,
            'student_answer': student_answer_clean,
            'score': student_answer_obj.score,
            'submitted_at': student_answer_obj.submitted_at.strftime('%Y-%m-%d %H:%M:%S'),
            'feedback': student_answer_obj.feedback
        }
        
        print(f"응답 데이터: {response_data}")
        print("=== 답안 체크 완료 ===")
        
        return JsonResponse(response_data)
        
    except Exception as e:
        # 예외 처리
        print(f"ERROR: 전체 예외 발생: {str(e)}")
        print(f"예외 타입: {type(e)}")
        
        # 더 자세한 에러 정보
        import traceback
        print(f"전체 트레이스백: {traceback.format_exc()}")
        
        return JsonResponse({
            'status': 'error',
            'message': f'서버 오류가 발생했습니다: {str(e)}',
            'jungoh': 'error'
        })



@login_required
@require_POST
def check_answer_0605(request):
    """답안 체크 AJAX 뷰"""
    try:
        # 사용자 인증 확인
        if not request.user.is_authenticated:
            return JsonResponse({
                'status': 'error',
                'message': '로그인이 필요합니다.',
                'jungoh': 'error'
            })
        
        # 요청 데이터 가져오기
        content_id = request.POST.get('content_id')
        student_answer = request.POST.get('student_answer')
        slide_id = request.POST.get('slide_id')
        is_resubmit = request.POST.get('is_resubmit', 'false').lower() == 'true'
        
        # 필수 데이터 검증
        if not all([content_id, student_answer, slide_id]):
            return JsonResponse({
                'status': 'error',
                'message': '필수 데이터가 누락되었습니다.',
                'jungoh': 'error'
            })
        
        # 객체 가져오기
        try:
            student = Student.objects.get(user=request.user)
            slide = ChasiSlide.objects.get(id=slide_id)
            content = Contents.objects.get(id=content_id)
        except Student.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': '학생 계정을 찾을 수 없습니다.',
                'jungoh': 'error'
            })
        except (ChasiSlide.DoesNotExist, Contents.DoesNotExist) as e:
            return JsonResponse({
                'status': 'error',
                'message': f'데이터를 찾을 수 없습니다: {str(e)}',
                'jungoh': 'error'
            })
        
        # 정답 비교
        correct_answer = content.answer.strip() if content.answer else ''
        student_answer_clean = student_answer.strip()
        
        # 정답 여부 판단
        is_correct = False
        if content.content_type.type_name in ['객관식', '선택형']:
            # 객관식: 정확히 일치
            is_correct = student_answer_clean == correct_answer
        elif content.content_type.type_name == '단답형':
            # 단답형: 대소문자 구분없이 비교 (필요에 따라 조정)
            is_correct = student_answer_clean.lower() == correct_answer.lower()
        
        # 답안 데이터 구성
        answer_data = {
            'selected_answer': student_answer_clean,
            'correct_answer': correct_answer,
            'answer_type': content.content_type.type_name,
            'submitted_at': timezone.now().isoformat()
        }
        
        # 데이터베이스에 저장/업데이트
        with transaction.atomic():
            if is_resubmit:
                # 재제출: 기존 답안 업데이트
                student_answer_obj, created = StudentAnswer.objects.get_or_create(
                    student=student,
                    slide=slide,
                    defaults={
                        'answer': answer_data,
                        'is_correct': is_correct,
                        'score': 100.0 if is_correct else 0.0,
                        'feedback': '자동 채점 결과'
                    }
                )
                if not created:
                    # 기존 답안 업데이트
                    student_answer_obj.answer = answer_data
                    student_answer_obj.is_correct = is_correct
                    student_answer_obj.score = 100.0 if is_correct else 0.0
                    student_answer_obj.submitted_at = timezone.now()
                    student_answer_obj.save()
            else:
                # 첫 제출: 새 답안 생성
                student_answer_obj = StudentAnswer.objects.create(
                    student=student,
                    slide=slide,
                    answer=answer_data,
                    is_correct=is_correct,
                    score=100.0 if is_correct else 0.0,
                    feedback='자동 채점 결과'
                )
        
        # 응답 데이터 구성
        response_data = {
            'status': 'success',
            'jungoh': 'right' if is_correct else 'wrong',
            'is_correct': is_correct,
            'correct_answer': correct_answer,
            'student_answer': student_answer_clean,
            'score': student_answer_obj.score,
            'submitted_at': student_answer_obj.submitted_at.strftime('%Y-%m-%d %H:%M:%S'),
            'feedback': student_answer_obj.feedback
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        # 예외 처리
        return JsonResponse({
            'status': 'error',
            'message': f'서버 오류가 발생했습니다: {str(e)}',
            'jungoh': 'error'
        })


