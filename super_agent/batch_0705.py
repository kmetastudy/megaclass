# super_agent/views.py
import json
import difflib
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db.models import Count, Q

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
        
        # JSON 파일 읽기
        try:
            content = file.read().decode('utf-8')
            data = json.loads(content)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': '올바른 JSON 형식이 아닙니다.'})
        except UnicodeDecodeError:
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
    """개별 항목 처리"""
    try:
        data = json.loads(request.body)
        item = data.get('item')
        
        if not item:
            return JsonResponse({'success': False, 'error': '항목 데이터가 없습니다.'})
        
        teacher = request.user.teacher
        
        # 1. 가장 유사한 차시 찾기
        chasi = find_similar_chasi(teacher, item['course'], item['chasi'])
        
        if not chasi:
            return JsonResponse({
                'success': False, 
                'error': f"'{item['course']} - {item['chasi']}'와 일치하는 차시를 찾을 수 없습니다."
            })
        
        # 2. 타입 매핑 (drag-1, drag-2 모두 drag로 통일)
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
        
        with transaction.atomic():
            if existing_slide:
                # 기존 슬라이드 업데이트
                content = existing_slide.content
                content.page = item['page']
                content.answer = json.dumps(item['answer'], ensure_ascii=False) if isinstance(item['answer'], dict) else item['answer']
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
                    answer=json.dumps(item['answer'], ensure_ascii=False) if isinstance(item['answer'], dict) else item['answer'],
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
            'message': f"'{title}' {'업데이트됨' if action == 'updated' else '생성됨'}"
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'처리 중 오류가 발생했습니다: {str(e)}'})

def find_similar_chasi(teacher, course_name, chasi_title):
    """유사한 차시 찾기"""
    # 먼저 정확한 매칭 시도
    chasis = Chasi.objects.filter(
        subject__teacher=teacher,
        subject__subject_name__icontains=course_name,
        chasi_title__icontains=chasi_title
    )
    
    if chasis.exists():
        return chasis.first()
    
    # 유사도 기반 매칭
    all_chasis = Chasi.objects.filter(
        subject__teacher=teacher
    ).select_related('subject')
    
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
    """교사의 전체 코스 구조 API"""
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
                        slides = ChasiSlide.objects.filter(chasi=chasi).order_by('slide_number')
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
                                'content_type': slide.content_type.type_name
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