# super_agent/ai_utils.py
# AI API 연동을 위한 유틸리티 함수들

import json
import requests
from datetime import datetime
from django.conf import settings

class AIProviderManager:
    """AI 프로바이더 관리 클래스"""
    
    def __init__(self):
        self.providers = {
            'claude': {
                'name': 'Claude (Anthropic)',
                'api_key': getattr(settings, 'CLAUDE_API_KEY', ''),
                'endpoint': 'https://api.anthropic.com/v1/messages',
                'model': 'claude-3-sonnet-20240229'
            },
            'chatgpt': {
                'name': 'ChatGPT (OpenAI)',
                'api_key': getattr(settings, 'OPENAI_API_KEY', ''),
                'endpoint': 'https://api.openai.com/v1/chat/completions',
                'model': 'gpt-4'
            },
            'gemini': {
                'name': 'Gemini (Google)',
                'api_key': getattr(settings, 'GEMINI_API_KEY', ''),
                'endpoint': 'https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent',
                'model': 'gemini-pro'
            },
            'grok': {
                'name': 'Grok (X.AI)',
                'api_key': getattr(settings, 'GROK_API_KEY', ''),
                'endpoint': 'https://api.x.ai/v1/chat/completions',
                'model': 'grok-beta'
            }
        }
    
    def generate_content(self, prompt, content_type, provider='claude', options=None):
        """AI를 이용한 콘텐츠 생성"""
        if options is None:
            options = {}
        
        # 프롬프트 최적화
        optimized_prompt = self._optimize_prompt(prompt, content_type, options)
        
        try:
            if provider == 'claude':
                return self._call_claude_api(optimized_prompt)
            elif provider == 'chatgpt':
                return self._call_chatgpt_api(optimized_prompt)
            elif provider == 'gemini':
                return self._call_gemini_api(optimized_prompt)
            elif provider == 'grok':
                return self._call_grok_api(optimized_prompt)
            else:
                return self._generate_mock_content(prompt, content_type, provider)
        
        except Exception as e:
            print(f"AI API 호출 오류 ({provider}): {str(e)}")
            return self._generate_mock_content(prompt, content_type, provider)
    
    def modify_content(self, original_content, modification_prompt, provider='claude'):
        """AI를 이용한 콘텐츠 수정"""
        full_prompt = f"""
기존 콘텐츠:
{original_content}

수정 요청:
{modification_prompt}

위 콘텐츠를 수정 요청에 따라 개선해주세요. HTML 형식을 유지하고, 기존 구조를 최대한 보존하면서 요청된 부분만 수정해주세요.
"""
        
        try:
            if provider == 'claude':
                return self._call_claude_api(full_prompt)
            elif provider == 'chatgpt':
                return self._call_chatgpt_api(full_prompt)
            elif provider == 'gemini':
                return self._call_gemini_api(full_prompt)
            elif provider == 'grok':
                return self._call_grok_api(full_prompt)
            else:
                return self._generate_mock_modification(original_content, modification_prompt, provider)
        
        except Exception as e:
            print(f"AI API 호출 오류 ({provider}): {str(e)}")
            return self._generate_mock_modification(original_content, modification_prompt, provider)
    
    def _optimize_prompt(self, prompt, content_type, options):
        """프롬프트 최적화"""
        
        # 기본 시스템 프롬프트
        system_prompt = """당신은 교육 콘텐츠 제작 전문가입니다. 
한국의 교육과정에 맞는 고품질의 교육 자료를 HTML 형식으로 제작해주세요.
반드시 다음 규칙을 따라주세요:
1. HTML 태그를 사용하여 구조화된 콘텐츠 제작
2. 교육적 가치가 높은 내용 구성
3. 학습자의 이해를 돕는 명확한 설명
4. 적절한 CSS 클래스 사용 (Bootstrap/Tailwind 호환)
"""
        
        # 콘텐츠 타입별 가이드라인
        type_guidelines = {
            '객관식': """
객관식 문제 형식:
- <div class="question"> 으로 감싸기
- 문제는 <h4> 태그 사용
- 선택지는 <ol type="1"> 사용
- 정답과 해설을 <div class="answer-section">에 포함
""",
            '단답형': """
단답형 문제 형식:
- <div class="question"> 으로 감싸기
- 답 입력란은 <input type="text" name="answer" class="form-input" /> 사용
- 정답을 <div class="answer-section">에 포함
""",
            '서술형': """
서술형 문제 형식:
- <div class="question"> 으로 감싸기
- 답안 작성란은 <textarea name="answer" rows="10" class="form-textarea"></textarea> 사용
- 채점 기준을 <div class="grading-criteria">에 포함
""",
            'presentation': """
프레젠테이션 형식:
- <div class="presentation"> 으로 감싸기
- 각 슬라이드는 <div class="slide"> 사용
- 제목, 내용, 이미지 영역을 구분하여 작성
"""
        }
        
        guideline = type_guidelines.get(content_type, "HTML 형식으로 교육 콘텐츠를 제작해주세요.")
        
        # 옵션 적용
        additional_instructions = []
        if options.get('include_explanation'):
            additional_instructions.append("상세한 해설을 포함해주세요.")
        if options.get('include_hints'):
            additional_instructions.append("학습자를 위한 힌트를 제공해주세요.")
        if options.get('include_images'):
            additional_instructions.append("이미지 플레이스홀더(<img> 태그)를 적절히 배치해주세요.")
        if options.get('multiple_versions'):
            additional_instructions.append("난이도가 다른 2-3가지 버전을 제공해주세요.")
        
        difficulty = options.get('difficulty', '중급')
        additional_instructions.append(f"난이도는 {difficulty} 수준으로 맞춰주세요.")
        
        # 최종 프롬프트 구성
        final_prompt = f"""{system_prompt}

콘텐츠 타입: {content_type}
{guideline}

사용자 요청:
{prompt}

추가 지시사항:
{' '.join(additional_instructions)}

HTML 형식으로 완성된 콘텐츠를 제작해주세요."""
        
        return final_prompt
    
    def _call_claude_api(self, prompt):
        """Claude API 호출"""
        provider_config = self.providers['claude']
        
        if not provider_config['api_key']:
            raise Exception("Claude API 키가 설정되지 않았습니다.")
        
        headers = {
            'x-api-key': provider_config['api_key'],
            'content-type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        
        data = {
            'model': provider_config['model'],
            'max_tokens': 4000,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        }
        
        response = requests.post(
            provider_config['endpoint'],
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['content'][0]['text']
        else:
            raise Exception(f"Claude API 오류: {response.status_code}")
    
    def _call_chatgpt_api(self, prompt):
        """ChatGPT API 호출"""
        provider_config = self.providers['chatgpt']
        
        if not provider_config['api_key']:
            raise Exception("OpenAI API 키가 설정되지 않았습니다.")
        
        headers = {
            'Authorization': f'Bearer {provider_config["api_key"]}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': provider_config['model'],
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'max_tokens': 4000,
            'temperature': 0.7
        }
        
        response = requests.post(
            provider_config['endpoint'],
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            raise Exception(f"ChatGPT API 오류: {response.status_code}")
    
    def _call_gemini_api(self, prompt):
        """Gemini API 호출"""
        provider_config = self.providers['gemini']
        
        if not provider_config['api_key']:
            raise Exception("Gemini API 키가 설정되지 않았습니다.")
        
        url = f"{provider_config['endpoint']}?key={provider_config['api_key']}"
        
        data = {
            'contents': [
                {
                    'parts': [
                        {'text': prompt}
                    ]
                }
            ]
        }
        
        response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            raise Exception(f"Gemini API 오류: {response.status_code}")
    
    def _call_grok_api(self, prompt):
        """Grok API 호출"""
        provider_config = self.providers['grok']
        
        if not provider_config['api_key']:
            raise Exception("Grok API 키가 설정되지 않았습니다.")
        
        headers = {
            'Authorization': f'Bearer {provider_config["api_key"]}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': provider_config['model'],
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'max_tokens': 4000,
            'temperature': 0.7
        }
        
        response = requests.post(
            provider_config['endpoint'],
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            raise Exception(f"Grok API 오류: {response.status_code}")
    
    def _generate_mock_content(self, prompt, content_type, provider):
        """모의 콘텐츠 생성 (API 키가 없거나 오류 시 사용)"""
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        if content_type == '객관식':
            return f'''<div class="question">
    <h4>문제: {prompt}</h4>
    <ol type="1">
        <li>첫 번째 선택지 (AI가 생성한 옵션)</li>
        <li>두 번째 선택지 (AI가 생성한 옵션)</li>
        <li>세 번째 선택지 (AI가 생성한 옵션)</li>
        <li>네 번째 선택지 (AI가 생성한 옵션)</li>
    </ol>
    <div class="answer-section mt-4 p-3 bg-blue-50 rounded">
        <p><strong>정답:</strong> 1번</p>
        <p><strong>해설:</strong> {provider}가 생성한 상세한 해설입니다. 이 문제는 {prompt}에 관한 내용으로, 첫 번째 선택지가 정답인 이유를 설명합니다.</p>
    </div>
</div>
<!-- Generated by {provider} at {timestamp} -->'''
        
        elif content_type == '단답형':
            return f'''<div class="question">
    <h4>문제: {prompt}</h4>
    <p class="mb-4">다음 빈칸에 알맞은 답을 써넣으시오.</p>
    <div class="answer-input mb-4">
        <label class="block mb-2">답: 
            <input type="text" name="answer" class="form-input w-full mt-1 px-3 py-2 border border-gray-300 rounded" />
        </label>
    </div>
    <div class="answer-section mt-4 p-3 bg-green-50 rounded">
        <p><strong>정답:</strong> {provider}가 생성한 답</p>
        <p><strong>해설:</strong> 이 문제의 답은 위와 같습니다. {prompt}에 관련된 핵심 개념을 이해하면 쉽게 풀 수 있습니다.</p>
    </div>
</div>
<!-- Generated by {provider} at {timestamp} -->'''
        
        elif content_type == '서술형':
            return f'''<div class="question">
    <h4>문제: {prompt}</h4>
    <p class="mb-4">다음 주제에 대해 자세히 서술하시오. (200자 이상)</p>
    <div class="answer-input mb-4">
        <textarea name="answer" rows="10" 
                  class="form-textarea w-full px-3 py-2 border border-gray-300 rounded" 
                  placeholder="답안을 작성하세요..."></textarea>
    </div>
    <div class="grading-criteria mt-4 p-3 bg-purple-50 rounded">
        <h5 class="font-semibold mb-2">채점 기준:</h5>
        <ul class="list-disc list-inside space-y-1">
            <li>개념의 정확한 이해 (30점)</li>
            <li>논리적 서술 구조 (30점)</li>
            <li>구체적 예시 제시 (20점)</li>
            <li>창의적 견해 표현 (20점)</li>
        </ul>
        <p class="mt-2"><strong>모범 답안 요소:</strong> {provider}가 생성한 {prompt}에 대한 핵심 요소들을 포함해야 합니다.</p>
    </div>
</div>
<!-- Generated by {provider} at {timestamp} -->'''
        
        else:
            return f'''<div class="content">
    <h3 class="text-xl font-bold mb-4">{provider}가 생성한 콘텐츠</h3>
    <div class="bg-gray-50 p-4 rounded-lg mb-4">
        <p><strong>사용자 요청:</strong> {prompt}</p>
        <p><strong>콘텐츠 타입:</strong> {content_type}</p>
        <p><strong>생성 AI:</strong> {provider}</p>
        <p><strong>생성 시간:</strong> {timestamp}</p>
    </div>
    <div class="prose max-w-none">
        <p>여기에 {content_type} 형태의 교육 콘텐츠가 {provider}에 의해 생성됩니다.</p>
        <p>실제 운영 환경에서는 AI API 키를 설정하여 진짜 AI가 생성한 콘텐츠를 받아볼 수 있습니다.</p>
        <h4>주요 특징:</h4>
        <ul>
            <li>사용자 맞춤형 콘텐츠</li>
            <li>교육과정 연계</li>
            <li>인터랙티브 요소 포함</li>
            <li>다양한 난이도 지원</li>
        </ul>
    </div>
</div>
<!-- Generated by {provider} at {timestamp} -->'''
    
    def _generate_mock_modification(self, original_content, modification_prompt, provider):
        """모의 콘텐츠 수정"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        modification_note = f'''
<div class="ai-modification-note" style="background: #f0f9ff; padding: 10px; margin: 10px 0; border-left: 4px solid #0ea5e9;">
    <small><strong>수정 내역 ({provider}):</strong> {modification_prompt}</small>
    <br><small><strong>수정 시간:</strong> {timestamp}</small>
</div>
'''
        
        return original_content + modification_note

# 글로벌 AI 매니저 인스턴스
ai_manager = AIProviderManager()


# ai_utils.py의 실제 API 호출 부분
#def _call_claude_api(self, prompt):
    # 실제 환경에서는 settings에서 API 키 확인 필요
#    if not provider_config['api_key']:
#        raise Exception("Claude API 키가 설정되지 않았습니다.")