import json
import base64
import re
from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from teacher.models import ContentType, Contents 

# OX 문항 HTML 템플릿
OX_TEMPLATE = """
<div class="quiz-container p-2 flex items-start justify-center">
    <div class="question-box p-2 w-full max-w-2xl mx-auto relative">
        <!-- 문제 제목 -->
        <div class="text-center mb-8">
            <h1 class="question-text text-2xl md:text-3xl font-bold text-gray-800 mb-4">
                {question_text}
            </h1>
            <div class="w-20 h-1 bg-gradient-to-r from-pink-500 to-purple-500 mx-auto rounded-full"></div>
        </div>
        <!-- 선택지 -->
        <div class="space-y-4 options-container">
            <div class="option-button bg-gray-50 border-2 border-gray-200 rounded-xl p-4 cursor-pointer flex items-center space-x-4 choice answer" data-clicked="1">
                <div class="flex-shrink-0">
                    <div class="w-12 h-12 bg-blue-500 text-white rounded-full flex items-center justify-center font-bold text-2xl">O</div>
                </div>
                <div class="option-text text-lg md:text-xl font-semibold text-gray-700">맞다</div>
            </div>
            <div class="option-button bg-gray-50 border-2 border-gray-200 rounded-xl p-4 cursor-pointer flex items-center space-x-4 choice answer" data-clicked="2">
                <div class="flex-shrink-0">
                    <div class="w-12 h-12 bg-red-500 text-white rounded-full flex items-center justify-center font-bold text-2xl">X</div>
                </div>
                <div class="option-text text-lg md:text-xl font-semibold text-gray-700">틀리다</div>
            </div>
        </div>
        <!-- 결과 표시 영역 -->
        <div class="text-center mt-8">
            <!-- 정답 GIF (평소에 숨김) -->
            <img id="right-gif" src="/static/img/jungoh/images/right.gif" alt="정답" class="result-gif mx-auto mb-4 hidden absolute top-10 left-10">
            
            <!-- 오답 GIF (평소에 숨김) -->
            <img id="wrong-gif" src="/static/img/jungoh/images/wrong.gif" alt="오답" class="result-gif mx-auto mb-4 hidden absolute top-10 left-10">
        </div>
    </div>
</div>
"""

# 5지선다 문항 HTML 템플릿
MULTI_CHOICE_TEMPLATE = """
<div class="quiz-container p-2 flex items-start justify-center font-sans">
    <div class="question-box p-4 sm:p-6 w-full max-w-3xl mx-auto relative bg-white rounded-xl shadow-lg">
        <div class="mb-6">
            <h1 class="question-text text-xl md:text-2xl font-bold text-gray-800 mb-4">
                {question_text}
            </h1>
        </div>

        <div class="space-y-3 options-container">
            <div class="option-button bg-gray-50 border-2 border-gray-200 rounded-xl p-3 cursor-pointer flex items-center space-x-4 hover:bg-gray-100 hover:border-blue-300 transition-all choice answer" data-clicked="1">
                <div class="flex-shrink-0">
                    <div class="w-10 h-10 bg-white border-2 border-gray-300 text-gray-600 rounded-full flex items-center justify-center font-bold text-xl">1</div>
                </div>
                <div class="option-text text-base md:text-lg font-semibold text-gray-700">① {option_1}</div>
            </div>
            <div class="option-button bg-gray-50 border-2 border-gray-200 rounded-xl p-3 cursor-pointer flex items-center space-x-4 hover:bg-gray-100 hover:border-blue-300 transition-all choice answer" data-clicked="2">
                <div class="flex-shrink-0">
                    <div class="w-10 h-10 bg-white border-2 border-gray-300 text-gray-600 rounded-full flex items-center justify-center font-bold text-xl">2</div>
                </div>
                <div class="option-text text-base md:text-lg font-semibold text-gray-700">② {option_2}</div>
            </div>
            <div class="option-button bg-gray-50 border-2 border-gray-200 rounded-xl p-3 cursor-pointer flex items-center space-x-4 hover:bg-gray-100 hover:border-blue-300 transition-all choice answer" data-clicked="3">
                <div class="flex-shrink-0">
                    <div class="w-10 h-10 bg-white border-2 border-gray-300 text-gray-600 rounded-full flex items-center justify-center font-bold text-xl">3</div>
                </div>
                <div class="option-text text-base md:text-lg font-semibold text-gray-700">③ {option_3}</div>
            </div>
            <div class="option-button bg-gray-50 border-2 border-gray-200 rounded-xl p-3 cursor-pointer flex items-center space-x-4 hover:bg-gray-100 hover:border-blue-300 transition-all choice answer" data-clicked="4">
                <div class="flex-shrink-0">
                    <div class="w-10 h-10 bg-white border-2 border-gray-300 text-gray-600 rounded-full flex items-center justify-center font-bold text-xl">4</div>
                </div>
                <div class="option-text text-base md:text-lg font-semibold text-gray-700">④ {option_4}</div>
            </div>
            <div class="option-button bg-gray-50 border-2 border-gray-200 rounded-xl p-3 cursor-pointer flex items-center space-x-4 hover:bg-gray-100 hover:border-blue-300 transition-all choice answer" data-clicked="5">
                <div class="flex-shrink-0">
                    <div class="w-10 h-10 bg-white border-2 border-gray-300 text-gray-600 rounded-full flex items-center justify-center font-bold text-xl">5</div>
                </div>
                <div class="option-text text-base md:text-lg font-semibold text-gray-700">⑤ {option_5}</div>
            </div>
        </div>
        
        <!-- 결과 표시 영역 -->
        <div class="text-center mt-8">
            <!-- 정답 GIF (평소에 숨김) -->
            <img id="right-gif" src="/static/img/jungoh/images/right.gif" alt="정답" class="result-gif mx-auto mb-4 hidden absolute top-10 left-10">
            
            <!-- 오답 GIF (평소에 숨김) -->
            <img id="wrong-gif" src="/static/img/jungoh/images/wrong.gif" alt="오답" class="result-gif mx-auto mb-4 hidden absolute top-10 left-10">
        </div>
    </div>
</div>
"""

def process_questions_json(questions_json, mindmap_json):
    """
    JSON 형태의 문항과 마인드맵을 처리하여 Contents 모델에 저장할 형태로 변환
    
    Args:
        questions_json: 문항 JSON 데이터 (dict 또는 list)
        mindmap_json: 마인드맵 JSON 데이터
    
    Returns:
        list: 생성할 문항 리스트
    """
    print("\n===== process_questions_json 시작 =====")
    print(f"questions_json 타입: {type(questions_json)}")
    print(f"mindmap_json 타입: {type(mindmap_json)}")
    
    generated_questions = []
    
    # 마인드맵에서 상위능력 찾기
    # 마인드맵이 {"수리능력": {...}} 형태인 경우
    if isinstance(mindmap_json, dict) and len(mindmap_json) > 0:
        main_competency = list(mindmap_json.keys())[0]  # 첫 번째 키를 상위역량으로
    else:
        main_competency = '직업기초능력'
    print(f"상위역량: {main_competency}")
    
    # 하위능력별 순서 카운터
    sub_competency_counters = {}
    
    # JSON 형식 확인 및 처리
    if isinstance(questions_json, list):
        print(f"리스트 형식 감지 - 길이: {len(questions_json)}")
        # 리스트 형식인 경우 - 각 항목이 {"name": "하위능력명", "ox": [...], "choice": [...]} 형태
        for idx, item in enumerate(questions_json):
            print(f"\n[리스트 항목 {idx}] 타입: {type(item)}")
            if isinstance(item, dict) and 'name' in item:
                sub_competency_name = item.get('name', f'하위능력{idx+1}')
                print(f"  하위능력: {sub_competency_name}")
                
                # 문항 데이터 구조 생성
                questions_data = {
                    'ox': item.get('ox', []),
                    'multi': item.get('choice', [])  # 'choice'를 'multi'로 매핑
                }
                
                process_sub_competency_questions(
                    sub_competency_name, questions_data, main_competency,
                    sub_competency_counters, generated_questions
                )
    elif isinstance(questions_json, dict):
        print(f"딕셔너리 형식 감지 - 키: {list(questions_json.keys())}")
        # 딕셔너리 형식인 경우
        for sub_competency_name, questions in questions_json.items():
            print(f"\n하위능력: {sub_competency_name}")
            process_sub_competency_questions(
                sub_competency_name, questions, main_competency,
                sub_competency_counters, generated_questions
            )
    else:
        print(f"오류: 예상하지 못한 형식 - {type(questions_json)}")
        raise ValueError("문항 JSON은 딕셔너리 또는 리스트 형식이어야 합니다.")
    
    print(f"\n총 생성된 문항 수: {len(generated_questions)}")
    print("===== process_questions_json 완료 =====\n")
    
    return generated_questions


def process_sub_competency_questions(sub_competency_name, questions, main_competency, 
                                    sub_competency_counters, generated_questions):
    """하위능력별 문항 처리"""
    print(f"\n  === {sub_competency_name} 처리 시작 ===")
    
    # 하위능력별 카운터 초기화
    if sub_competency_name not in sub_competency_counters:
        sub_competency_counters[sub_competency_name] = 0
        print(f"  카운터 초기화: {sub_competency_name} = 0")
    
    # OX 문제 처리
    ox_questions = questions.get('ox', []) if isinstance(questions, dict) else []
    print(f"  OX 문항 수: {len(ox_questions)}")
    
    for idx, ox_q in enumerate(ox_questions):
        sub_competency_counters[sub_competency_name] += 1
        
        question_id = f"q_{sub_competency_name}_{sub_competency_counters[sub_competency_name]}"
        print(f"    OX문항 {idx+1}: {question_id}")
        print(f"      문제: {ox_q.get('question', '')[:50]}...")
        print(f"      정답: {ox_q.get('answer', 'O')}")
        
        # HTML 생성 (question_id 파라미터 제거)
        html = OX_TEMPLATE.format(
            question_text=ox_q.get('question', '')
        )
        
        # 정답 JSON - O는 1, X는 2로 변환
        ox_answer = ox_q.get('answer', 'O')
        answer_value = "1" if ox_answer == "O" else "2"
        
        # solution 또는 explanation 필드 처리
        solution_text = ox_q.get('solution', ox_q.get('explanation', f'이 문항은 {sub_competency_name}을(를) 평가하는 OX 문항입니다.'))
        
        answer_json = {
            "answer": answer_value,
            "solution": f"정답: {ox_answer}\n\n{solution_text}"
        }
        
        # 태그 생성
        tags = {
            "competency": main_competency,  # 상위 역량
            "sub_competency": sub_competency_name,  # 하위 역량
            "difficulty": ox_q.get('difficulty', '중'),
            "question_type": "ox",
            "order": sub_competency_counters[sub_competency_name]
        }
        
        generated_questions.append({
            "title": f"{sub_competency_name} {sub_competency_counters[sub_competency_name]}",
            "question_html": html,
            "answer_json": json.dumps(answer_json, ensure_ascii=False),
            "tags_json": json.dumps(tags, ensure_ascii=False),
            "content_type": "multiple-choice"
        })
        print(f"      → 문항 생성 완료")
    
    # 5지선다 문제 처리
    multi_questions = questions.get('multi', []) if isinstance(questions, dict) else []
    print(f"  5지선다 문항 수: {len(multi_questions)}")
    
    for idx, multi_q in enumerate(multi_questions):
        sub_competency_counters[sub_competency_name] += 1
        
        question_id = f"q_{sub_competency_name}_{sub_competency_counters[sub_competency_name]}"
        print(f"    5지선다 {idx+1}: {question_id}")
        print(f"      문제: {multi_q.get('question', '')[:50]}...")
        print(f"      정답: {multi_q.get('answer', 1)}")
        
        # HTML 생성 (question_id 파라미터 제거)
        # options 또는 choices 필드 처리
        options = multi_q.get('options', multi_q.get('choices', [''] * 5))
        html = MULTI_CHOICE_TEMPLATE.format(
            question_text=multi_q.get('question', ''),
            option_1=options[0] if len(options) > 0 else '',
            option_2=options[1] if len(options) > 1 else '',
            option_3=options[2] if len(options) > 2 else '',
            option_4=options[3] if len(options) > 3 else '',
            option_5=options[4] if len(options) > 4 else ''
        )
        
        # 정답 JSON
        answer_num = str(multi_q.get('answer', 1))
        
        # solution 또는 explanation 필드 처리
        solution_text = multi_q.get('solution', multi_q.get('explanation', f'이 문항은 {sub_competency_name}을(를) 평가하는 5지선다 문항입니다.'))
        
        answer_json = {
            "answer": answer_num,
            "solution": f"정답: {answer_num}\n\n{solution_text}"
        }
        
        # 태그 생성
        tags = {
            "competency": main_competency,  # 상위 역량
            "sub_competency": sub_competency_name,  # 하위 역량
            "difficulty": multi_q.get('difficulty', '중'),
            "question_type": "multi",
            "order": sub_competency_counters[sub_competency_name]
        }
        
        generated_questions.append({
            "title": f"{sub_competency_name} {sub_competency_counters[sub_competency_name]}",
            "question_html": html,
            "answer_json": json.dumps(answer_json, ensure_ascii=False),
            "tags_json": json.dumps(tags, ensure_ascii=False),
            "content_type": "multiple-choice"
        })
        print(f"      → 문항 생성 완료")
    
    print(f"  === {sub_competency_name} 처리 완료 - 총 {sub_competency_counters[sub_competency_name]}문항 ===\n")


class QuestionAgentView(View):
    """메인 페이지를 렌더링하는 뷰"""
    def get(self, request, *args, **kwargs):
        return render(request, 'super_agent/index.html')


@csrf_exempt
def process_files(request):
    """AJAX 요청을 받아 JSON 파일을 처리하고 문항을 생성하는 뷰"""
    print("\n========== process_files 시작 ==========")
    print(f"요청 메소드: {request.method}")
    
    if request.method == 'POST':
        try:
            questions_file = request.FILES.get('questions_file')
            mindmap_file = request.FILES.get('mindmap_file')
            
            print(f"questions_file: {questions_file}")
            print(f"mindmap_file: {mindmap_file}")

            if not questions_file:
                print("오류: 문항 JSON 파일 없음")
                return JsonResponse({'status': 'error', 'message': '문항 JSON 파일을 업로드해주세요.'}, status=400)
            
            if not mindmap_file:
                print("오류: 마인드맵 JSON 파일 없음")
                return JsonResponse({'status': 'error', 'message': '마인드맵 JSON 파일을 업로드해주세요.'}, status=400)

            # JSON 파일 읽기
            try:
                questions_content = questions_file.read().decode('utf-8')
                print(f"\n문항 파일 내용 (첫 200자): {questions_content[:200]}...")
                questions_json = json.loads(questions_content)
                print(f"문항 JSON 파싱 성공")
            except json.JSONDecodeError as e:
                print(f"문항 JSON 파싱 오류: {str(e)}")
                return JsonResponse({'status': 'error', 'message': f'문항 JSON 파일 형식 오류: {str(e)}'}, status=400)
            
            try:
                mindmap_content = mindmap_file.read().decode('utf-8')
                print(f"\n마인드맵 파일 내용 (첫 200자): {mindmap_content[:200]}...")
                mindmap_json = json.loads(mindmap_content)
                print(f"마인드맵 JSON 파싱 성공")
            except json.JSONDecodeError as e:
                print(f"마인드맵 JSON 파싱 오류: {str(e)}")
                return JsonResponse({'status': 'error', 'message': f'마인드맵 JSON 파일 형식 오류: {str(e)}'}, status=400)

            # JSON 데이터 처리
            print("\nJSON 처리 시작...")
            generated_questions = process_questions_json(questions_json, mindmap_json)
            print(f"처리 완료 - 생성된 문항 수: {len(generated_questions)}")

            # multiple-choice ContentType 가져오기
            content_type, created = ContentType.objects.get_or_create(
                type_name='multiple-choice',
                defaults={'description': '객관식 문항 (OX, 5지선다)'}
            )
            print(f"ContentType: {content_type.type_name} (새로 생성: {created})")

            # DB에 저장
            saved_count = 0
            competency_name = mindmap_json.get('name', '직업기초능력')
            
            print("\nDB 저장 시작...")
            for idx, item in enumerate(generated_questions):
                try:
                    content = Contents.objects.create(
                        content_type=content_type,
                        title=item['title'],
                        page=item['question_html'],
                        answer=item['answer_json'],
                        tags=json.loads(item['tags_json']),
                        created_by=request.user if request.user.is_authenticated else None
                    )
                    saved_count += 1
                    print(f"  [{idx+1}] {item['title']} - 저장 성공 (ID: {content.id})")
                except Exception as e:
                    print(f"  [{idx+1}] {item['title']} - 저장 실패: {str(e)}")
            
            print(f"\nDB 저장 완료 - 성공: {saved_count}/{len(generated_questions)}")
            
            response_data = {
                'status': 'success', 
                'message': f'{saved_count}개의 문항이 성공적으로 저장되었습니다.',
                'competency': competency_name
            }
            print(f"응답 데이터: {response_data}")
            print("========== process_files 완료 ==========\n")
            
            return JsonResponse(response_data)

        except Exception as e:
            import traceback
            print(f"\n!!! 예외 발생 !!!")
            print(f"오류: {str(e)}")
            print(traceback.format_exc())
            print("!!!!!!!!!!!!!!!!!!\n")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    print("오류: POST 요청이 아님")
    return JsonResponse({'status': 'error', 'message': '잘못된 요청입니다.'}, status=400)


def get_question_tree(request):
    """생성된 문항들을 태그 기반의 트리 구조로 반환하는 뷰"""
    print("\n===== get_question_tree 시작 =====")
    
    # multiple-choice 타입의 콘텐츠만 필터링
    content_type = ContentType.objects.filter(type_name='multiple-choice').first()
    if not content_type:
        print("ContentType 'multiple-choice' 없음")
        return JsonResponse({})
    
    print(f"ContentType 찾음: {content_type.type_name} (ID: {content_type.id})")

    questions = Contents.objects.filter(content_type=content_type).order_by('created_at')
    print(f"전체 문항 수: {questions.count()}")
    
    # 직업기초능력별로 트리 구조 생성
    tree_data = {}
    for q in questions:
        competency = q.tags.get('competency', '기타')
        sub_competency = q.tags.get('sub_competency', '기타')
        order = q.tags.get('order', 0)
        question_type = q.tags.get('question_type', 'unknown')

        if competency not in tree_data:
            tree_data[competency] = {}
        
        if sub_competency not in tree_data[competency]:
            tree_data[competency][sub_competency] = []
        
        tree_data[competency][sub_competency].append({
            'id': q.id,
            'title': q.title,
            'order': order,
            'type': question_type
        })
        
    # 각 하위 역량별로 순서대로 정렬
    for competency in tree_data:
        for sub_competency in tree_data[competency]:
            tree_data[competency][sub_competency].sort(key=lambda x: x['order'])
    
    print(f"트리 구조: {len(tree_data)}개 역량")
    for comp, subs in tree_data.items():
        print(f"  - {comp}: {len(subs)}개 하위역량")
    
    print("===== get_question_tree 완료 =====\n")
    return JsonResponse(tree_data)