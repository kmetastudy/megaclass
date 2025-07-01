from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db.models import Q
from django.utils import timezone

from django.db import models
import json
import os
import uuid
import traceback

# 모델 임포트
from .models import Contents_Template
from teacher.models import Contents, ContentType, ContentTypeCategory, Course, Chapter,ContentsAttached

# import google as genai
# import google.generativeai as genai
# from django.conf import settings
# import re
# Gemini API 설정
# genai.configure(api_key=settings.GEMINI_API_KEY)
####### 구글 비전 api 세팅#################

from google import genai

client = genai.Client(api_key="AIzaSyAP04dk1CIbnhvtCqVuxIWRXr03ff_Cnqo")



@login_required
@require_http_methods(["POST"])
def upload_image(request):
    """이미지 업로드 API"""
    try:
        # 파일 검증
        if 'file' not in request.FILES:
            return JsonResponse({'error': '파일이 없습니다.'}, status=400)
        
        file = request.FILES['file']
        original_name = request.POST.get('original_name', file.name)
        file_type = request.POST.get('file_type', file.content_type)
        file_size = request.POST.get('file_size', file.size)
        content_id = request.POST.get('content_id')
        
        # 파일 크기 검증 (10MB)
        if file.size > 10 * 1024 * 1024:
            return JsonResponse({'error': '파일 크기는 10MB 이하여야 합니다.'}, status=400)
        
        # 파일 타입 검증
        if not file.content_type.startswith('image/'):
            return JsonResponse({'error': '이미지 파일만 업로드 가능합니다.'}, status=400)
        
        # 고유한 파일명 생성
        file_extension = os.path.splitext(original_name)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # 파일 저장
        file_path = f"contents/attachments/{request.user.id}/{unique_filename}"
        saved_path = default_storage.save(file_path, ContentFile(file.read()))
        
        # ContentsAttached 객체 생성
        attachment = ContentsAttached.objects.create(
            contents_id=content_id if content_id else None,
            file=saved_path,
            original_name=original_name,
            file_type=file_type,
            file_size=int(file_size),
            uploaded_by=request.user,
            is_temporary=True if not content_id else False
        )
        
        return JsonResponse({
            'success': True,
            'attachment_id': attachment.id,
            'file_url': default_storage.url(saved_path),
            'original_name': original_name,
            'file_size': file_size
        })
        
    except Exception as e:
        print(f"이미지 업로드 오류: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({'error': f'업로드 중 오류가 발생했습니다: {str(e)}'}, status=500)


@login_required
@require_http_methods(["DELETE"])
def cleanup_temp_upload(request, attachment_id):
    """임시 업로드 파일 정리"""
    try:
        attachment = get_object_or_404(
            ContentsAttached, 
            id=attachment_id, 
            uploaded_by=request.user,
            is_temporary=True
        )
        
        # 파일 삭제
        if attachment.file:
            default_storage.delete(attachment.file.name)
        
        # DB 레코드 삭제
        attachment.delete()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        print(f"파일 정리 오류: {str(e)}")
        return JsonResponse({'error': f'파일 정리 중 오류가 발생했습니다: {str(e)}'}, status=500)


@login_required
@require_http_methods(["GET"])
def get_categories(request):
    """카테고리 목록 조회"""
    try:
        categories = ContentTypeCategory.objects.all().values('id', 'category_name')
        return JsonResponse(list(categories), safe=False)
    except Exception as e:
        print(f"카테고리 조회 오류: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_content_types(request):
    """컨텐츠 타입 목록 조회"""
    try:
        category_id = request.GET.get('category')
        
        if category_id:
            content_types = ContentType.objects.filter(
                category_name_id=category_id, 
                is_active=True
            ).values('id', 'type_name')
        else:
            content_types = ContentType.objects.filter(
                is_active=True
            ).values('id', 'type_name')
            
        return JsonResponse(list(content_types), safe=False)
    except Exception as e:
        print(f"컨텐츠 타입 조회 오류: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_courses(request):
    """코스 목록 조회"""
    try:
        courses = Course.objects.filter(
            teacher__user=request.user,
            is_active=True
        ).values('id', 'subject_name', 'target')
        return JsonResponse(list(courses), safe=False)
    except Exception as e:
        print(f"코스 조회 오류: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_course_chapters(request, course_id):
    """특정 코스의 챕터 목록 조회"""
    try:
        chapters = Chapter.objects.filter(
            subject_id=course_id
        ).values('id', 'chapter_title', 'chapter_order').order_by('chapter_order')
        return JsonResponse(list(chapters), safe=False)
    except Exception as e:
        print(f"챕터 조회 오류: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def search_contents(request):
    """컨텐츠 검색 (teacher.Contents 모델 사용)"""
    try:
        # 필터 파라미터
        category = request.GET.get('category')
        content_type = request.GET.get('type')
        course = request.GET.get('course')
        chapter = request.GET.get('chapter')
        search = request.GET.get('search')
        
        # 기본 쿼리셋
        queryset = Contents.objects.filter(
            created_by=request.user,
            is_active=True
        )
        
        # 필터 적용
        if category:
            queryset = queryset.filter(content_type__category_name_id=category)
        
        if content_type:
            queryset = queryset.filter(content_type_id=content_type)
        
        if search:
            queryset = queryset.filter(title__icontains=search)
        
        # 결과 반환
        contents = queryset.select_related('content_type').values(
            'id', 'title', 'content_type__type_name', 'created_at'
        ).order_by('-created_at')[:50]
        
        # 날짜 포맷팅
        for content in contents:
            content['content_type_name'] = content.pop('content_type__type_name')
            content['created_at'] = content['created_at'].strftime('%Y-%m-%d')
        
        return JsonResponse(list(contents), safe=False)
        
    except Exception as e:
        print(f"컨텐츠 검색 오류: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def search_templates(request):
    """템플릿 검색 (Contents_Template 모델 사용)"""
    try:
        print(f"=== 템플릿 검색 요청 ===")
        print(f"요청자: {request.user}")
        
        # 필터 파라미터
        category = request.GET.get('category')
        content_type = request.GET.get('type')
        search = request.GET.get('search')
        
        print(f"필터: category={category}, type={content_type}, search={search}")
        
        # 기본 쿼리셋 (공개 템플릿 + 내가 만든 템플릿)
        queryset = Contents_Template.objects.filter(
            is_active=True
        ).filter(
            Q(is_public=True) | Q(created_by=request.user)
        )
        
        # 필터 적용
        if category:
            queryset = queryset.filter(content_category_id=category)
        
        if content_type:
            queryset = queryset.filter(content_type_id=content_type)
        
        if search:
            queryset = queryset.filter(title__icontains=search)
        
        # 결과 반환
        templates = queryset.select_related('content_type', 'content_category').values(
            'id', 'title', 'content_type__type_name', 'content_category__category_name',
            'created_at', 'page', 'answer', 'meta_data', 'tags'
        ).order_by('-created_at')[:50]
        
        # 날짜 포맷팅
        for template in templates:
            template['content_type_name'] = template.pop('content_type__type_name')
            template['category_name'] = template.pop('content_category__category_name')
            template['created_at'] = template['created_at'].strftime('%Y-%m-%d')
        
        print(f"검색 결과: {len(templates)}개")
        return JsonResponse(list(templates), safe=False)
        
    except Exception as e:
        print(f"템플릿 검색 오류: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_content(request, content_id):
    """특정 컨텐츠 조회 (teacher.Contents 모델)"""
    try:
        content = get_object_or_404(
            Contents, 
            id=content_id, 
            created_by=request.user
        )
        
        return JsonResponse({
            'id': content.id,
            'title': content.title,
            'content_type': content.content_type_id,
            'page': content.page,
            'answer': content.answer,
            'meta_data': content.meta_data,
            'tags': content.tags,
            'prompt': getattr(content, 'prompt', ''),
        })
        
    except Exception as e:
        print(f"컨텐츠 조회 오류: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_template(request, template_id):
    """특정 템플릿 조회 (Contents_Template 모델)"""
    try:
        template = get_object_or_404(
            Contents_Template, 
            id=template_id
        )
        
        # 권한 확인 (공개 템플릿이거나 내가 만든 템플릿)
        if not (template.is_public or template.created_by == request.user):
            return JsonResponse({'error': '접근 권한이 없습니다.'}, status=403)
        
        return JsonResponse({
            'id': template.id,
            'title': template.title,
            'content_category': template.content_category_id,
            'content_type': template.content_type_id,
            'page': template.page,
            'answer': template.answer,
            'meta_data': template.meta_data,
            'tags': template.tags,
            'is_public': template.is_public,
            'created_by': template.created_by.username if template.created_by else None,
        })
        
    except Exception as e:
        print(f"템플릿 조회 오류: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


###########################################################################################
###  새로 만들어진 generate_content 함수
###########################################################################################
import google as genai
from django.conf import settings
import json
import re

# Gemini API 설정
# genai.configure(api_key=settings.GEMINI_API_KEY)
@login_required
@require_http_methods(["POST"])
def generate_content(request):
    """AI 컨텐츠 생성 (Gemini 연동) - 사용자 태그 우선, 없으면 AI 생성"""
    try:
        data = json.loads(request.body)
        print(f"AI 생성 요청: {data}")
        
        # 필수 데이터 검증
        title = data.get('title', '')
        content_type_id = data.get('content_type')
        prompt = data.get('prompt', '')
        template_id = data.get('template_id')
        answer_input = data.get('answer_input', '{}')
        
        # 중요: 사용자가 입력한 태그 확인
        user_tags = data.get('tags', '{}').strip()
        
        if not prompt.strip():
            return JsonResponse({'error': '문항 생성 지시사항을 입력해주세요.'}, status=400)
        
        # 템플릿 가져오기
        template_html = ""
        template_answer = "{}"
        template_meta = "{}"
        template_tags = "{}"
        
        if template_id:
            try:
                template = Contents_Template.objects.get(
                    id=template_id,
                    is_active=True
                )
                # 권한 확인 (공개 템플릿이거나 내가 만든 템플릿)
                if template.is_public or template.created_by == request.user:
                    template_html = template.page
                    template_answer = template.answer or "{}"
                    template_meta = json.dumps(template.meta_data)
                    template_tags = json.dumps(template.tags)
                    
                    # 조회수 증가
                    template.view_count += 1
                    template.save()
                    
            except Contents_Template.DoesNotExist:
                pass
        
        # ContentType 정보 가져오기
        content_type_info = ""
        if content_type_id:
            try:
                content_type = ContentType.objects.get(id=content_type_id)
                content_type_info = f"{content_type.category_name.category_name} - {content_type.type_name}"
            except ContentType.DoesNotExist:
                pass
        
        # 사용자 태그 확인 및 처리
        def has_meaningful_user_tags(tags_str):
            """사용자가 의미있는 태그를 입력했는지 확인"""
            try:
                if not tags_str or tags_str.strip() in ['{}', '']:
                    return False
                tags_obj = json.loads(tags_str)
                # 기본값이 아닌 실제 내용이 있는지 확인
                if isinstance(tags_obj, dict) and len(tags_obj) > 0:
                    # 기본 템플릿과 다른 값이 있는지 확인
                    default_keys = ['competency', 'sub_competency', 'difficulty', 'question_type', 'order']
                    has_custom_content = any(key in tags_obj for key in tags_obj.keys() if key not in default_keys) or \
                                       any(tags_obj.get(key) not in ['수리능력', '도표분석능력', '중', 'multiple-choice', 1] 
                                           for key in default_keys if key in tags_obj)
                    return has_custom_content
                return False
            except:
                return False
        
        def generate_tags_from_prompt(prompt_text, content_type_info):
            """프롬프트 기반 태그 생성"""
            # 기본 태그 구조
            tags = {
                "competency": "수리능력",
                "sub_competency": "도표분석능력", 
                "difficulty": "중",
                "question_type": "multiple-choice",
                "order": 1
            }
            
            prompt_lower = prompt_text.lower()
            
            # 역량 추론
            if any(keyword in prompt_lower for keyword in ['수학', '계산', '도표', '그래프', '차트', '통계']):
                tags["competency"] = "수리능력"
                if any(keyword in prompt_lower for keyword in ['도표', '그래프', '차트']):
                    tags["sub_competency"] = "도표분석능력"
                elif any(keyword in prompt_lower for keyword in ['계산', '연산', '공식']):
                    tags["sub_competency"] = "수치연산능력"
                else:
                    tags["sub_competency"] = "수리추론능력"
            elif any(keyword in prompt_lower for keyword in ['언어', '문해', '읽기', '쓰기', '국어', '어학']):
                tags["competency"] = "언어능력"
                tags["sub_competency"] = "언어이해능력"
            elif any(keyword in prompt_lower for keyword in ['창의', '사고', '문제해결', '논리']):
                tags["competency"] = "창의적사고능력"
                tags["sub_competency"] = "문제해결능력"
            elif any(keyword in prompt_lower for keyword in ['과학', '실험', '자연', '물리', '화학', '생물']):
                tags["competency"] = "과학적사고능력"
                tags["sub_competency"] = "과학적추론능력"
            
            # 난이도 추론
            if any(keyword in prompt_lower for keyword in ['쉬운', '기초', '초급', '간단한']):
                tags["difficulty"] = "하"
            elif any(keyword in prompt_lower for keyword in ['어려운', '고급', '심화', '복잡한']):
                tags["difficulty"] = "상"
            else:
                tags["difficulty"] = "중"
            
            # 문제 타입 추론
            if any(keyword in prompt_lower for keyword in ['객관식', '선택지', '4지선다', '5지선다', '다지선다']):
                tags["question_type"] = "multiple-choice"
            elif any(keyword in prompt_lower for keyword in ['주관식', '서술', '단답', '논술']):
                tags["question_type"] = "short-answer"
            elif any(keyword in prompt_lower for keyword in ['참/거짓', 'true/false', 'ox', '참거짓']):
                tags["question_type"] = "true-false"
            elif any(keyword in prompt_lower for keyword in ['빈칸', '완성', '채우기']):
                tags["question_type"] = "fill-in-blank"
            else:
                # 콘텐츠 타입에서 추론
                if '객관식' in content_type_info:
                    tags["question_type"] = "multiple-choice"
                elif '주관식' in content_type_info:
                    tags["question_type"] = "short-answer"
            
            return tags
        
        # 사용자 태그 처리 결정
        use_user_tags = has_meaningful_user_tags(user_tags)
        
        if use_user_tags:
            print(f"사용자가 입력한 태그 사용: {user_tags}")
            final_tags = user_tags
        else:
            print(f"프롬프트 기반 태그 생성 시작")
            generated_tags = generate_tags_from_prompt(prompt, content_type_info)
            final_tags = json.dumps(generated_tags, ensure_ascii=False)
            print(f"생성된 태그: {final_tags}")
        
        # Gemini 프롬프트 구성
        tags_instruction = ""
        if use_user_tags:
            tags_instruction = f"""
            **사용자 지정 태그** (반드시 이 형식을 유지하세요):
            {final_tags}
            """
        else:
            tags_instruction = f"""
            **태그 생성 지침**:
            다음 형식에 맞춰 태그를 생성하세요:
            - competency: 역량 (수리능력, 언어능력, 창의적사고능력 등)
            - sub_competency: 세부 역량
            - difficulty: 난이도 (하, 중, 상)
            - question_type: 문제 유형 (multiple-choice, short-answer, true-false 등)
            - order: 순서 (숫자)
            
            프롬프트 내용을 분석하여 적절한 태그를 생성하세요.
            """
        
        system_prompt = f"""
            당신은 교육 문항 생성 전문가입니다. 주어진 요구사항에 따라 고품질의 교육 문항을 생성해주세요.

            **문항 타입**: {content_type_info}
            **문항 제목**: {title}

            **템플릿 구조** (참고용):
            {template_html if template_html else "템플릿이 지정되지 않았습니다. 적절한 HTML 구조를 만들어주세요."}

            **답안 형식** (참고용):
            {template_answer}

            {tags_instruction}

            **생성 규칙**:
            1. HTML은 깔끔하고 접근성을 고려하여 작성
            2. 문제는 명확하고 이해하기 쉽게 구성
            3. 선택지나 답안은 교육적으로 의미있게 구성
            4. 답안 JSON은 정확한 형식으로 제공
            5. 이미지가 필요한 경우 placeholder를 사용
            6. 한국어로 생성

            **사용자 요청사항**:
            {prompt}

            응답은 다음 JSON 형식으로만 제공해주세요:
            {{
                "page": "생성된 HTML 콘텐츠",
                "answer": "정답 JSON 문자열",
                "meta_data": "메타데이터 JSON 문자열",
                "tags": "태그/평가기준 JSON 문자열"
            }}
            """

        # Gemini API 호출
        json_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[system_prompt],
        )
        ai_response = json_response.text.strip()
        
        # JSON 추출 (```json 태그 제거)
        json_match = re.search(r'```json\s*(.*?)\s*```', ai_response, re.DOTALL)
        if json_match:
            ai_response = json_match.group(1)
        elif ai_response.startswith('{') and ai_response.endswith('}'):
            pass
        else:
            # JSON 형식이 아닌 경우 기본 구조로 감싸기
            fallback_data = {
                "page": ai_response,
                "answer": template_answer,
                "meta_data": template_meta or '{"difficulty": "중", "estimated_time": 300}',
                "tags": final_tags
            }
            ai_response = json.dumps(fallback_data, ensure_ascii=False)
        
        try:
            result = json.loads(ai_response)
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 기본값 사용
            result = {
                "page": f"<div class='ai-generated-content'><h2>{title}</h2><p>{ai_response}</p></div>",
                "answer": template_answer,
                "meta_data": '{"difficulty": "중", "estimated_time": 300}',
                "tags": final_tags
            }
        
        # 답안 입력값이 있으면 덮어쓰기
        if answer_input and answer_input.strip() != '{}':
            try:
                answer_data = json.loads(answer_input)
                result['answer'] = json.dumps(answer_data, ensure_ascii=False)
            except json.JSONDecodeError:
                pass
        
        # 태그 최종 처리
        if use_user_tags:
            # 사용자 태그 사용
            result['tags'] = final_tags
        else:
            # AI 생성 태그 확인 및 보정
            try:
                ai_tags = json.loads(result.get('tags', '{}'))
                if not ai_tags or not isinstance(ai_tags, dict) or not ai_tags.get('competency'):
                    # AI가 제대로 생성하지 못했으면 프롬프트 기반 생성 태그 사용
                    result['tags'] = final_tags
            except (json.JSONDecodeError, KeyError):
                result['tags'] = final_tags
        
        # 메타데이터 보강
        meta_data = {}
        if result.get('meta_data'):
            try:
                meta_data = json.loads(result['meta_data'])
            except:
                pass
        
        meta_data.update({
            'generated_by': 'gemini',
            'generated_at': timezone.now().isoformat(),
            'content_type': content_type_info,
            'template_used': bool(template_id),
            'user_tags_used': use_user_tags
        })
        result['meta_data'] = json.dumps(meta_data, ensure_ascii=False)
        
        print(f"AI 생성 결과: {result}")
        return JsonResponse(result)
        
    except Exception as e:
        print(f"AI 생성 오류: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        
        # 오류 시 기본 응답
        fallback_tags = {
            "competency": "수리능력",
            "sub_competency": "도표분석능력",
            "difficulty": "중",
            "question_type": "multiple-choice",
            "order": 1
        }
        
        fallback_response = {
            'page': f'<div class="error-fallback"><h2>{data.get("title", "생성된 문항")}</h2><p>AI 생성 중 오류가 발생했습니다. 수동으로 편집해주세요.</p></div>',
            'answer': '{"correct": "", "explanation": "답안을 입력해주세요"}',
            'meta_data': '{"difficulty": "medium", "estimated_time": 300}',
            'tags': json.dumps(fallback_tags, ensure_ascii=False)
        }
        
        return JsonResponse(fallback_response)

@login_required
@require_http_methods(["POST"])
def generate_content_0629(request):
    """AI 컨텐츠 생성 (임시 구현)"""
    try:
        data = json.loads(request.body)
        print(f"AI 생성 요청: {data}")
        
        # 실제로는 AI API를 호출해야 하지만, 임시로 더미 데이터 반환
        return JsonResponse({
            'page': f'<h1>{data.get("title", "생성된 문항")}</h1><p>AI가 생성한 컨텐츠입니다.</p>',
            'answer': '{"correct": "A", "explanation": "AI가 생성한 설명입니다."}',
            'meta_data': '{"difficulty": "medium", "time": "15"}',
            'tags': '{"skills": ["problem_solving"], "topics": ["general"]}'
        })
        
    except Exception as e:
        print(f"AI 생성 오류: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def create_content(request):
    """컨텐츠 생성 (teacher.Contents 모델)"""
    try:
        data = json.loads(request.body)
        print(f"컨텐츠 생성 요청: {data}")
        
        content = Contents.objects.create(
            title=data['title'],
            content_type_id=data['content_type'],
            page=data['page'],
            answer=data.get('answer', ''),
            meta_data=json.loads(data.get('meta_data', '{}')),
            tags=json.loads(data.get('tags', '{}')),
            created_by=request.user
        )
        
        # 임시 첨부파일들을 이 컨텐츠와 연결
        ContentsAttached.objects.filter(
            uploaded_by=request.user,
            is_temporary=True,
            contents__isnull=True
        ).update(
            contents=content,
            is_temporary=False
        )
        
        return JsonResponse({
            'id': content.id,
            'title': content.title,
            'message': '컨텐츠가 생성되었습니다.'
        })
        
    except Exception as e:
        print(f"컨텐츠 생성 오류: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["PUT"])
def update_content(request, content_id):
    """컨텐츠 수정 (teacher.Contents 모델)"""
    try:
        content = get_object_or_404(
            Contents, 
            id=content_id, 
            created_by=request.user
        )
        
        data = json.loads(request.body)
        print(f"컨텐츠 수정 요청: {data}")
        
        content.title = data['title']
        content.content_type_id = data['content_type']
        content.page = data['page']
        content.answer = data.get('answer', '')
        content.meta_data = json.loads(data.get('meta_data', '{}'))
        content.tags = json.loads(data.get('tags', '{}'))
        content.save()
        
        # 임시 첨부파일들을 이 컨텐츠와 연결
        ContentsAttached.objects.filter(
            uploaded_by=request.user,
            is_temporary=True,
            contents__isnull=True
        ).update(
            contents=content,
            is_temporary=False
        )
        
        return JsonResponse({
            'id': content.id,
            'title': content.title,
            'message': '컨텐츠가 수정되었습니다.'
        })
        
    except Exception as e:
        print(f"컨텐츠 수정 오류: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def create_template(request):
    """템플릿 생성 (Contents_Template 모델)"""
    print(f"=== 템플릿 생성 요청 시작 ===")
    print(f"요청자: {request.user}")
    print(f"Content-Type: {request.content_type}")
    print(f"Request body: {request.body}")
    
    try:
        # JSON 파싱
        try:
            data = json.loads(request.body)
            print(f"파싱된 데이터: {data}")
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류: {e}")
            return JsonResponse({'error': f'잘못된 JSON 형식입니다: {str(e)}'}, status=400)
        
        # 필수 필드 검증
        required_fields = ['title', 'content_category', 'content_type']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            error_msg = f'필수 필드가 누락되었습니다: {", ".join(missing_fields)}'
            print(f"필수 필드 누락: {missing_fields}")
            return JsonResponse({'error': error_msg}, status=400)
        
        # 외래키 유효성 검증
        try:
            category = ContentTypeCategory.objects.get(id=data['content_category'])
            content_type = ContentType.objects.get(id=data['content_type'])
            print(f"카테고리: {category}, 타입: {content_type}")
        except ContentTypeCategory.DoesNotExist:
            return JsonResponse({'error': f'존재하지 않는 카테고리입니다: {data["content_category"]}'}, status=400)
        except ContentType.DoesNotExist:
            return JsonResponse({'error': f'존재하지 않는 컨텐츠 타입입니다: {data["content_type"]}'}, status=400)
        
        # JSON 필드 파싱
        try:
            # meta_data 처리
            meta_data_str = data.get('meta_data', '{}')
            if isinstance(meta_data_str, str):
                meta_data = json.loads(meta_data_str) if meta_data_str.strip() else {}
            else:
                meta_data = meta_data_str
            
            # answer 처리
            answer_str = data.get('answer', '{}')
            if isinstance(answer_str, str) and answer_str.strip().startswith('{'):
                # JSON 형태의 답안은 그대로 문자열로 저장
                answer = answer_str
            else:
                answer = answer_str
            
            # tags 처리 - JavaScript 코드를 포함할 수 있음
            tags_str = data.get('tags', '{}')
            if tags_str.strip().startswith('{'):
                # JSON 형태
                tags = json.loads(tags_str)
            else:
                # JavaScript 코드 또는 일반 텍스트
                tags = {"javascript": tags_str}
            
            print(f"처리된 데이터: meta_data={meta_data}, answer길이={len(answer)}, tags={tags}")
            
        except json.JSONDecodeError as e:
            print(f"JSON 필드 파싱 오류: {e}")
            return JsonResponse({'error': f'JSON 데이터 파싱 오류: {str(e)}'}, status=400)
        
        # 템플릿 생성
        template = Contents_Template.objects.create(
            title=data['title'],
            content_category=category,
            content_type=content_type,
            page=data.get('page', ''),
            answer=answer,
            meta_data=meta_data,
            tags=tags,
            is_public=data.get('is_public', True),
            created_by=request.user
        )
        
        print(f"템플릿 생성 성공: ID={template.id}")
        
        return JsonResponse({
            'id': template.id,
            'title': template.title,
            'message': '템플릿이 생성되었습니다.'
        })
        
    except Exception as e:
        print(f"템플릿 생성 오류: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({'error': f'템플릿 생성 중 오류가 발생했습니다: {str(e)}'}, status=500)


@login_required
@require_http_methods(["PUT"])
def update_template(request, template_id):
    """템플릿 수정 (Contents_Template 모델)"""
    try:
        template = get_object_or_404(
            Contents_Template, 
            id=template_id, 
            created_by=request.user
        )
        
        data = json.loads(request.body)
        print(f"템플릿 수정 요청: {data}")
        
        # 외래키 유효성 검증
        if 'content_category' in data:
            try:
                category = ContentTypeCategory.objects.get(id=data['content_category'])
                template.content_category = category
            except ContentTypeCategory.DoesNotExist:
                return JsonResponse({'error': f'존재하지 않는 카테고리입니다: {data["content_category"]}'}, status=400)
        
        if 'content_type' in data:
            try:
                content_type = ContentType.objects.get(id=data['content_type'])
                template.content_type = content_type
            except ContentType.DoesNotExist:
                return JsonResponse({'error': f'존재하지 않는 컨텐츠 타입입니다: {data["content_type"]}'}, status=400)
        
        # 일반 필드 업데이트
        if 'title' in data:
            template.title = data['title']
        if 'page' in data:
            template.page = data['page']
        if 'answer' in data:
            template.answer = data['answer']
        if 'is_public' in data:
            template.is_public = data['is_public']
        
        # JSON 필드 업데이트
        if 'meta_data' in data:
            meta_data_str = data['meta_data']
            if isinstance(meta_data_str, str):
                template.meta_data = json.loads(meta_data_str) if meta_data_str.strip() else {}
            else:
                template.meta_data = meta_data_str
        
        if 'tags' in data:
            tags_str = data['tags']
            if tags_str.strip().startswith('{'):
                template.tags = json.loads(tags_str)
            else:
                template.tags = {"javascript": tags_str}
        
        template.save()
        
        return JsonResponse({
            'id': template.id,
            'title': template.title,
            'message': '템플릿이 수정되었습니다.'
        })
        
    except Exception as e:
        print(f"템플릿 수정 오류: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["DELETE"])
def delete_template(request, template_id):
    """템플릿 삭제 (Contents_Template 모델)"""
    try:
        template = get_object_or_404(
            Contents_Template, 
            id=template_id, 
            created_by=request.user
        )
        
        template_title = template.title
        template.delete()
        
        return JsonResponse({
            'message': f'템플릿 "{template_title}"이 삭제되었습니다.'
        })
        
    except Exception as e:
        print(f"템플릿 삭제 오류: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


# CP Agent 메인 페이지
@login_required
def cp_agent_view(request):
    """CP Agent 메인 페이지"""
    return render(request, 'cp/cp_agent.html')