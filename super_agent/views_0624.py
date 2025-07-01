import json
import base64
from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# 'teacher' 앱의 모델을 가져옵니다. 실제 프로젝트 구조에 맞게 경로를 수정해야 할 수 있습니다.
from teacher.models import ContentType, Contents 

# --- Gemini API 호출 시뮬레이션 ---
# 실제 환경에서는 google.generativeai와 같은 라이브러리를 사용하여 API를 호출해야 합니다.
# 여기서는 API가 반환할 것으로 예상되는 데이터 구조를 시뮬레이션합니다.
def call_gemini_api_mock(pdf_text, mindmap_image_base64, multi_choice_template, ox_template):
    """
    Gemini API 호출을 시뮬레이션하는 함수입니다.
    실제로는 여기서 API 요청을 보내고 응답을 받습니다.
    """
    print("--- Calling Simulated Gemini API ---")
    # print("PDF Text:", pdf_text[:100]) # Log first 100 chars
    # print("Mindmap Image (base64):", mindmap_image_base64[:30]) # Log first 30 chars
    
    # Gemini가 반환할 것으로 예상되는 데이터의 모의(Mock) 응답입니다.
    mock_response = [
        {
            "question_html": """<div class="text-center mb-8"><h1 class="question-text text-2xl md:text-3xl font-bold text-gray-800 mb-4">다음 중 의사소통능력의 하위 능력이 아닌 것은?</h1> ... (HTML 내용 생략) ... </div>""",
            "answer_json": json.dumps({"answer": "5", "solution": "문제해결능력은 별개의 직업기초능력입니다."}),
            "tags_json": json.dumps({"category": "의사소통능력", "sub_category": "하위 능력", "difficulty": "하"})
        },
        {
            "question_html": """<div class="text-center mb-8"><h1 class="question-text text-2xl md:text-3xl font-bold text-gray-800 mb-4">의사소통은 조직의 생산성 증진에 기여한다.</h1> ... (HTML 내용 생략) ... </div>""",
            "answer_json": json.dumps({"answer": "1", "solution": "O. 원활한 의사소통은 조직의 생산성, 구성원 사기 진작에 직접적인 영향을 미칩니다."}),
            "tags_json": json.dumps({"category": "의사소통능력", "sub_category": "중요성", "difficulty": "하"})
        },
        {
            "question_html": """<div class="text-center mb-8"><h1 class="question-text text-2xl md:text-3xl font-bold text-gray-800 mb-4">문서이해를 위한 첫 단계는 무엇인가?</h1> ... (HTML 내용 생략) ... </div>""",
            "answer_json": json.dumps({"answer": "3", "solution": "문서의 목적을 먼저 이해해야 전체적인 내용을 정확히 파악할 수 있습니다."}),
            "tags_json": json.dumps({"category": "문서이해능력", "sub_category": "문서 이해 절차", "difficulty": "중"})
        }
    ]
    
    return mock_response


class QuestionAgentView(View):
    """메인 페이지를 렌더링하는 뷰"""
    def get(self, request, *args, **kwargs):
        return render(request, 'super_agent/index.html')

@csrf_exempt # 실제 프로덕션에서는 CSRF 보호를 활성화해야 합니다.
def process_files(request):
    """AJAX 요청을 받아 파일을 처리하고 문항을 생성하는 뷰"""
    if request.method == 'POST':
        try:
            pdf_file = request.FILES.get('pdf_file')
            mindmap_file = request.FILES.get('mindmap_file')

            if not pdf_file or not mindmap_file:
                return JsonResponse({'status': 'error', 'message': 'PDF와 마인드맵 파일을 모두 업로드해주세요.'}, status=400)

            # 파일 내용 읽기
            pdf_text = pdf_file.read().decode('utf-8', errors='ignore')
            mindmap_image_base64 = base64.b64encode(mindmap_file.read()).decode('utf-8')

            # 이전 프롬프트에서 제공된 문제 템플릿 (실제로는 DB나 설정에서 관리)
            multi_choice_template = "..." # 오지선다 HTML 템플릿
            ox_template = "..." # OX HTML 템플릿

            # Gemini API 호출 (현재는 모의 함수 사용)
            generated_questions = call_gemini_api_mock(pdf_text, mindmap_image_base64, multi_choice_template, ox_template)

            # DB에 저장
            # '문제' ContentType이 있다고 가정합니다. 없으면 생성합니다.
            content_type, _ = ContentType.objects.get_or_create(type_name='자동 생성 문제')

            saved_count = 0
            for item in generated_questions:
                tags = json.loads(item['tags_json'])
                
                Contents.objects.create(
                    content_type=content_type,
                    title=f"{tags.get('category', '미분류')}-{tags.get('sub_category','소분류')}",
                    page=item['question_html'],
                    answer=item['answer_json'],
                    tags=tags,
                    created_by=request.user if request.user.is_authenticated else None
                )
                saved_count += 1
            
            return JsonResponse({'status': 'success', 'message': f'{saved_count}개의 문항이 성공적으로 생성되었습니다.'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': '잘못된 요청입니다.'}, status=400)


def get_question_tree(request):
    """생성된 문항들을 태그 기반의 트리 구조로 반환하는 뷰"""
    # '자동 생성 문제' 타입의 콘텐츠만 가져옵니다.
    content_type = ContentType.objects.filter(type_name='자동 생성 문제').first()
    if not content_type:
        return JsonResponse({})

    questions = Contents.objects.filter(content_type=content_type).order_by('created_at')
    
    # 태그를 기반으로 트리 구조 생성
    tree_data = {}
    for q in questions:
        category = q.tags.get('category', '기타')
        sub_category = q.tags.get('sub_category', '기타')

        if category not in tree_data:
            tree_data[category] = {}
        
        if sub_category not in tree_data[category]:
            tree_data[category][sub_category] = []
        
        tree_data[category][sub_category].append({
            'id': q.id,
            'title': q.title
        })

    return JsonResponse(tree_data)