# super_agent/batch.py
import json
import difflib
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db.models import Count, Q
# 기존 import들 다음에 추가:
from teacher.models import ContentsAttached  # 새로 추가된 모델
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import mimetypes
import os
from django.conf import settings

# Teacher 앱의 모델들 import
from teacher.models import Course, Chapter, SubChapter, Chasi, ChasiSlide, ContentType, Contents
from teacher.decorators import teacher_required

@login_required
def index(request):
    """기본 인덱스 뷰 (기존)"""
    return render(request, 'super_agent/index.html')

@login_required
@teacher_required
def batch_process_view(request):
    """배치 처리 메인 페이지"""
    teacher = request.user.teacher
    
    # 교사의 코스 목록
    courses = Course.objects.filter(teacher=teacher).order_by('-created_at')
    
    context = {
        'courses': courses,
        'teacher': teacher,
    }
    
    return render(request, 'super_agent/batch.html', context)

@login_required
@teacher_required
@require_http_methods(["POST"])
def api_batch_upload(request):
    """JSON 파일 업로드 및 검증"""
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'success': False, 'error': '파일이 선택되지 않았습니다.'})
        
        file = request.FILES['file']
        
        if not file.name.endswith('.json'):
            return JsonResponse({'success': False, 'error': 'JSON 파일만 업로드 가능합니다.'})
        
        # JSON 파일 읽기 - UTF-8 인코딩 강제 적용
        try:
            content = file.read().decode('utf-8')
            data = json.loads(content)
        except json.JSONDecodeError as e:
            return JsonResponse({'success': False, 'error': f'올바른 JSON 형식이 아닙니다: {str(e)}'})
        except UnicodeDecodeError:
            try:
                # UTF-8 실패 시 다른 인코딩 시도
                file.seek(0)
                content = file.read().decode('utf-8-sig')  # BOM 포함 UTF-8
                data = json.loads(content)
            except:
                try:
                    file.seek(0)
                    content = file.read().decode('cp949')  # 한국어 인코딩
                    data = json.loads(content)
                except:
                    return JsonResponse({'success': False, 'error': '파일 인코딩 오류입니다. UTF-8로 저장해주세요.'})
        
        # 데이터 검증
        if not isinstance(data, list):
            return JsonResponse({'success': False, 'error': 'JSON은 배열 형태여야 합니다.'})
        
        if not data:
            return JsonResponse({'success': False, 'error': '비어있는 파일입니다.'})
        
        # 필수 키 검증
        required_keys = ['course', 'chasi', 'type', 'page', 'answer']
        invalid_items = []
        
        for i, item in enumerate(data):
            missing_keys = [key for key in required_keys if key not in item]
            if missing_keys:
                invalid_items.append({
                    'index': i + 1,
                    'missing_keys': missing_keys
                })
        
        if invalid_items:
            return JsonResponse({
                'success': False, 
                'error': '필수 키가 누락된 항목이 있습니다.',
                'invalid_items': invalid_items
            })
        
        # 타입 매핑 검증
        type_mapping = {
            'ox': 'ox-quiz',
            'choice': 'choice',
            'selection': 'selection', 
            'drag-1': 'drag',
            'drag-2': 'drag',
            'line_matching': 'line_matching'
        }
        
        unsupported_types = []
        for i, item in enumerate(data):
            if item['type'] not in type_mapping:
                unsupported_types.append({
                    'index': i + 1,
                    'type': item['type']
                })
        
        if unsupported_types:
            return JsonResponse({
                'success': False,
                'error': '지원하지 않는 타입이 있습니다.',
                'unsupported_types': unsupported_types,
                'supported_types': list(type_mapping.keys())
            })
        
        return JsonResponse({
            'success': True,
            'message': f'{len(data)}개 항목이 성공적으로 업로드되었습니다.',
            'data': data,
            'total_items': len(data)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'파일 처리 중 오류가 발생했습니다: {str(e)}'})

@login_required
@teacher_required
@require_http_methods(["POST"])
def api_batch_process_item(request):
    """개별 항목 처리 - 한글 처리 개선"""
    try:
        data = json.loads(request.body)
        item = data.get('item')
        
        if not item:
            return JsonResponse({'success': False, 'error': '항목 데이터가 없습니다.'})
        
        teacher = request.user.teacher
        
        # 1. 가장 유사한 차시 찾기 (선택된 코스 고려)
        selected_course_id = data.get('selected_course_id')
        chasi = find_similar_chasi(teacher, item['course'], item['chasi'], selected_course_id)
        
        if not chasi:
            return JsonResponse({
                'success': False, 
                'error': f"'{item['course']} - {item['chasi']}'와 일치하는 차시를 찾을 수 없습니다."
            })
        
        # 2. 타입 매핑
        type_mapping = {
            'ox': 'ox-quiz',
            'choice': 'choice',
            'selection': 'selection',
            'drag-1': 'drag',
            'drag-2': 'drag',
            'line_matching': 'line_matching'
        }
        
        content_type_name = type_mapping[item['type']]
        
        # 3. ContentType 찾기
        try:
            content_type = ContentType.objects.get(type_name=content_type_name)
        except ContentType.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f"ContentType '{content_type_name}'을 찾을 수 없습니다."
            })
        
        # 4. 제목 생성 (drag-1, drag-2 구분을 위해 원본 타입 사용)
        title = f"{item['chasi']} - {item['type']}"
        
        # 5. 기존 슬라이드 확인 (ContentType + 제목으로 정확한 매칭)
        existing_slide = ChasiSlide.objects.filter(
            chasi=chasi,
            content_type=content_type,
            slide_title=title
        ).first()
        
        # 기존 슬라이드가 없다면 Content title로도 한번 더 확인
        if not existing_slide:
            existing_content = Contents.objects.filter(
                title=title,
                content_type=content_type,
                created_by=request.user
            ).first()
            
            if existing_content:
                existing_slide = ChasiSlide.objects.filter(
                    chasi=chasi,
                    content=existing_content
                ).first()
        
        # 6. answer 데이터 처리 - 한글 유니코드 디코딩
        answer_data = item['answer']
        if isinstance(answer_data, dict):
            # solution 필드의 유니코드 이스케이프 시퀀스 처리
            if 'solution' in answer_data and isinstance(answer_data['solution'], str):
                solution_text = answer_data['solution']
                # 유니코드 이스케이프 시퀀스가 있으면 디코딩
                if '\\u' in solution_text:
                    try:
                        # JSON 문자열로 래핑하여 유니코드 디코딩
                        decoded_solution = json.loads(f'"{solution_text}"')
                        answer_data['solution'] = decoded_solution
                    except json.JSONDecodeError:
                        # 디코딩 실패 시 원본 유지
                        pass
            
            # JSON으로 직렬화할 때 한글이 제대로 보이도록 ensure_ascii=False 사용
            answer_json = json.dumps(answer_data, ensure_ascii=False, indent=2)
        else:
            answer_json = str(answer_data)
        
        with transaction.atomic():
            if existing_slide:
                # 기존 슬라이드 업데이트
                content = existing_slide.content
                content.page = item['page']
                content.answer = answer_json
                content.title = title
                content.save()
                
                existing_slide.slide_title = title
                existing_slide.save()
                
                action = 'updated'
                slide_id = existing_slide.id
                content_id = content.id
                
            else:
                # 새 Content 생성
                content = Contents.objects.create(
                    content_type=content_type,
                    title=title,
                    page=item['page'],
                    answer=answer_json,
                    created_by=request.user,
                    is_active=True,
                    is_public=False
                )
                
                # 새 ChasiSlide 생성
                last_slide = ChasiSlide.objects.filter(chasi=chasi).order_by('-slide_number').first()
                slide_number = (last_slide.slide_number + 1) if last_slide else 1
                
                slide = ChasiSlide.objects.create(
                    chasi=chasi,
                    slide_number=slide_number,
                    slide_title=title,
                    content_type=content_type,
                    content=content,
                    estimated_time=5,
                    is_active=True
                )
                
                action = 'created'
                slide_id = slide.id
                content_id = content.id
        
        return JsonResponse({
            'success': True,
            'action': action,
            'chasi_id': chasi.id,
            'chasi_title': chasi.chasi_title,
            'slide_id': slide_id,
            'content_id': content_id,
            'title': title,
            'content_type': content_type_name,
            'slide_number': slide_number if action == 'created' else existing_slide.slide_number,
            'message': f"'{title}' {'업데이트됨' if action == 'updated' else '생성됨'}"
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'처리 중 오류가 발생했습니다: {str(e)}'})

def find_similar_chasi(teacher, course_name, chasi_title, selected_course_id=None):
    """유사한 차시 찾기 (코스 선택 시 해당 코스로 제한)"""
    
    # 기본 쿼리셋
    base_queryset = Chasi.objects.filter(
        subject__teacher=teacher
    ).select_related('subject')
    
    # 선택된 코스가 있다면 해당 코스로 제한
    if selected_course_id:
        try:
            selected_course_id = int(selected_course_id)
            base_queryset = base_queryset.filter(subject_id=selected_course_id)
        except (ValueError, TypeError):
            pass
    
    # 먼저 정확한 매칭 시도
    chasis = base_queryset.filter(
        subject__subject_name__icontains=course_name,
        chasi_title__icontains=chasi_title
    )
    
    if chasis.exists():
        return chasis.first()
    
    # 유사도 기반 매칭
    all_chasis = base_queryset.all()
    
    best_match = None
    best_score = 0
    
    for chasi in all_chasis:
        # 코스명과 차시명 유사도 계산
        course_similarity = difflib.SequenceMatcher(
            None, course_name.lower(), chasi.subject.subject_name.lower()
        ).ratio()
        
        chasi_similarity = difflib.SequenceMatcher(
            None, chasi_title.lower(), chasi.chasi_title.lower()
        ).ratio()
        
        # 가중 평균 (차시명에 더 높은 가중치)
        total_score = (course_similarity * 0.3) + (chasi_similarity * 0.7)
        
        if total_score > best_score and total_score > 0.6:  # 60% 이상 유사도
            best_score = total_score
            best_match = chasi
    
    return best_match

@login_required
@teacher_required
def api_courses_structure(request):
    """교사의 전체 코스 구조 API - 성능 최적화"""
    try:
        teacher = request.user.teacher
        
        courses_data = []
        courses = Course.objects.filter(teacher=teacher).order_by('subject_name')
        
        for course in courses:
            course_data = {
                'id': course.id,
                'subject_name': course.subject_name,
                'target': course.target,
                'chapters': []
            }
            
            chapters = Chapter.objects.filter(subject=course).order_by('chapter_order')
            for chapter in chapters:
                chapter_data = {
                    'id': chapter.id,
                    'title': chapter.chapter_title,
                    'order': chapter.chapter_order,
                    'subchapters': []
                }
                
                subchapters = SubChapter.objects.filter(chapter=chapter).order_by('sub_chapter_order')
                for subchapter in subchapters:
                    subchapter_data = {
                        'id': subchapter.id,
                        'title': subchapter.sub_chapter_title,
                        'order': subchapter.sub_chapter_order,
                        'chasis': []
                    }
                    
                    chasis = Chasi.objects.filter(sub_chapter=subchapter).order_by('chasi_order')
                    for chasi in chasis:
                        slides = ChasiSlide.objects.filter(chasi=chasi).order_by('slide_number').select_related('content', 'content_type')
                        chasi_data = {
                            'id': chasi.id,
                            'title': chasi.chasi_title,
                            'order': chasi.chasi_order,
                            'slides': []
                        }
                        
                        for slide in slides:
                            chasi_data['slides'].append({
                                'id': slide.id,
                                'title': slide.slide_title,
                                'slide_number': slide.slide_number,
                                'content_type': slide.content_type.type_name,
                                'content_id': slide.content.id if slide.content else None,
                                'estimated_time': slide.estimated_time,
                                'is_active': slide.is_active
                            })
                        
                        subchapter_data['chasis'].append(chasi_data)
                    
                    chapter_data['subchapters'].append(subchapter_data)
                
                course_data['chapters'].append(chapter_data)
            
            courses_data.append(course_data)
        
        return JsonResponse({
            'success': True,
            'courses': courses_data
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@teacher_required
@require_http_methods(["GET"])
def api_slide_preview(request, slide_id):
    """슬라이드 미리보기 API"""
    try:
        teacher = request.user.teacher
        
        # 교사의 슬라이드인지 확인
        slide = get_object_or_404(
            ChasiSlide.objects.select_related('content', 'content_type', 'chasi', 'chasi__subject'),
            id=slide_id,
            chasi__subject__teacher=teacher
        )
        
        # answer 데이터 파싱
        answer_data = {}
        if slide.content and slide.content.answer:
            try:
                answer_data = json.loads(slide.content.answer)
            except json.JSONDecodeError:
                answer_data = {'raw': slide.content.answer}
        
        slide_data = {
            'id': slide.id,
            'title': slide.slide_title,
            'slide_number': slide.slide_number,
            'content_type': slide.content_type.type_name if slide.content_type else None,
            'estimated_time': slide.estimated_time,
            'is_active': slide.is_active,
            'chasi': {
                'id': slide.chasi.id,
                'title': slide.chasi.chasi_title,
                'course': slide.chasi.subject.subject_name
            },
            'content': {
                'id': slide.content.id if slide.content else None,
                'page': slide.content.page if slide.content else None,
                'answer': answer_data,
                'created_at': slide.content.created_at.isoformat() if slide.content else None,
                'updated_at': slide.content.updated_at.isoformat() if slide.content else None,
            } if slide.content else None
        }
        
        return JsonResponse({
            'success': True,
            'slide': slide_data
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@teacher_required  
@require_http_methods(["GET"])
def api_processing_status(request):
    """처리 상태 확인 API (실시간 상태 체크용)"""
    try:
        # 세션이나 캐시에서 처리 상태를 가져올 수 있습니다
        # 여기서는 간단한 응답만 제공
        return JsonResponse({
            'success': True,
            'is_processing': False,  # 실제로는 세션/캐시에서 가져와야 함
            'current_progress': 0,
            'total_items': 0
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    

@login_required
@teacher_required
@require_http_methods(["POST"])
def api_content_update(request, content_id):
    """콘텐츠 업데이트 API"""
    try:
        data = json.loads(request.body)
        teacher = request.user.teacher
        
        # 교사의 콘텐츠인지 확인
        content = get_object_or_404(
            Contents,
            id=content_id,
            created_by=request.user
        )
        
        # 업데이트할 필드들
        if 'page' in data:
            content.page = data['page']
        if 'answer' in data:
            content.answer = data['answer']
        if 'meta_data' in data:
            content.meta_data = data['meta_data']
        if 'tags' in data:
            content.tags = data['tags']
            
        content.save()
        
        return JsonResponse({
            'success': True,
            'message': '콘텐츠가 성공적으로 업데이트되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': str(e)
        }, status=500)
    

# super_agent/batch.py

# ... (other imports)

@login_required
@teacher_required
@require_http_methods(["POST"])
def api_slide_update(request, slide_id):
    """슬라이드 자체의 정보를 업데이트하는 API (예: 예상 소요 시간)"""
    try:
        data = json.loads(request.body)
        teacher = request.user.teacher

        # 교사의 슬라이드인지 확인
        slide = get_object_or_404(
            ChasiSlide,
            id=slide_id,
            chasi__subject__teacher=teacher
        )

        if 'estimated_time' in data:
            slide.estimated_time = int(data['estimated_time'])
        
        # 다른 슬라이드 필드도 필요한 경우 여기에 추가
        # if 'slide_title' in data:
        #     slide.slide_title = data['slide_title']

        slide.save()

        return JsonResponse({
            'success': True,
            'message': '슬라이드가 성공적으로 업데이트되었습니다.'
        })

    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': str(e)
        }, status=500)


# super_agent/batch.py에 추가할 API 함수들

@login_required
@teacher_required
@require_http_methods(["POST"])
def api_upload_temporary_file(request):
    """임시 파일 업로드 API"""
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'success': False, 'error': '파일이 선택되지 않았습니다.'})
        
        file = request.FILES['file']
        
        # 파일 타입 검증 (이미지만 허용)
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
        if file.content_type not in allowed_types:
            return JsonResponse({'success': False, 'error': '지원하지 않는 파일 형식입니다.'})
        
        # 파일 크기 검증 (5MB 제한)
        if file.size > 5 * 1024 * 1024:
            return JsonResponse({'success': False, 'error': '파일 크기는 5MB를 초과할 수 없습니다.'})
        
        # 임시 첨부파일 생성
        attachment = ContentsAttached.objects.create(
            file=file,
            original_name=file.name,
            file_type=file.content_type,
            file_size=file.size,
            is_temporary=True,
            uploaded_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'attachment_id': attachment.id,
            'file_url': attachment.file.url,
            'original_name': attachment.original_name,
            'file_size': attachment.file_size
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'파일 업로드 중 오류가 발생했습니다: {str(e)}'})


@login_required
@teacher_required
@require_http_methods(["POST"])
def api_delete_temporary_file(request):
    """임시 파일 삭제 API"""
    try:
        data = json.loads(request.body)
        attachment_id = data.get('attachment_id')
        
        if not attachment_id:
            return JsonResponse({'success': False, 'error': '첨부파일 ID가 필요합니다.'})
        
        # 사용자의 임시 파일인지 확인
        attachment = get_object_or_404(
            ContentsAttached,
            id=attachment_id,
            uploaded_by=request.user,
            is_temporary=True
        )
        
        attachment.delete()
        
        return JsonResponse({
            'success': True,
            'message': '파일이 성공적으로 삭제되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'파일 삭제 중 오류가 발생했습니다: {str(e)}'})


@login_required
@teacher_required
@require_http_methods(["POST"])
def api_finalize_attachments(request, content_id):
    """임시 첨부파일들을 최종 확정하는 API"""
    try:
        data = json.loads(request.body)
        attachment_ids = data.get('attachment_ids', [])
        
        teacher = request.user.teacher
        
        # 콘텐츠 소유권 확인
        content = get_object_or_404(
            Contents,
            id=content_id,
            created_by=request.user
        )
        
        # 임시 첨부파일들을 최종 확정
        updated_count = ContentsAttached.objects.filter(
            id__in=attachment_ids,
            uploaded_by=request.user,
            is_temporary=True
        ).update(
            contents=content,
            is_temporary=False
        )
        
        return JsonResponse({
            'success': True,
            'message': f'{updated_count}개 파일이 최종 확정되었습니다.',
            'updated_count': updated_count
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'파일 확정 중 오류가 발생했습니다: {str(e)}'})


# 사용하지 않는 임시 파일들을 정리하는 태스크 (선택사항)
from django.utils import timezone
from datetime import timedelta

def cleanup_temporary_files():
    """24시간 이상 된 임시 파일들을 정리"""
    cutoff_time = timezone.now() - timedelta(hours=24)
    old_temp_files = ContentsAttached.objects.filter(
        is_temporary=True,
        uploaded_at__lt=cutoff_time
    )
    
    count = 0
    for attachment in old_temp_files:
        attachment.delete()
        count += 1
    
    return count