"""
이메일 전송 관련 기능 및 API
Django SMTP를 사용한 문의 이메일 전송
"""
import json
import re
from datetime import datetime
from django.http import JsonResponse
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.utils.html import escape
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.middleware.csrf import get_token
import logging

logger = logging.getLogger(__name__)


def validate_email_data(data):
    """
    이메일 데이터 유효성 검사
    
    Args:
        data (dict): 폼 데이터
        
    Returns:
        tuple: (is_valid: bool, errors: list)
    """
    errors = []
    
    # 필수 필드 확인
    required_fields = ['schoolName', 'teacherName', 'phone', 'email']
    for field in required_fields:
        if not data.get(field) or not data.get(field).strip():
            errors.append(f"{field}은(는) 필수 입력 항목입니다.")
    
    # 길이 제한 확인
    if data.get('schoolName') and len(data.get('schoolName')) > 100:
        errors.append("학교명은 100자를 초과할 수 없습니다.")
    
    if data.get('teacherName') and len(data.get('teacherName')) > 100:
        errors.append("이름은 100자를 초과할 수 없습니다.")
    
    if data.get('phone') and len(data.get('phone')) > 20:
        errors.append("전화번호는 20자를 초과할 수 없습니다.")
    
    if data.get('email') and len(data.get('email')) > 254:
        errors.append("이메일은 254자를 초과할 수 없습니다.")
    
    if data.get('inquiry') and len(data.get('inquiry')) > 2000:
        errors.append("문의내용은 2000자를 초과할 수 없습니다.")
    
    # 이메일 형식 검증
    if data.get('email'):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data.get('email')):
            errors.append("올바른 이메일 형식이 아닙니다.")
    
    # 전화번호 형식 검증 (한국 전화번호)
    if data.get('phone'):
        phone_pattern = r'^\d{2,3}-\d{3,4}-\d{4}$'
        if not re.match(phone_pattern, data.get('phone')):
            errors.append("전화번호는 '010-1234-5678' 형식으로 입력해주세요.")
    
    # Honeypot 필드 확인 (봇 방지)
    if data.get('website'):  # honeypot 필드
        errors.append("잘못된 요청입니다.")
    
    return len(errors) == 0, errors


def format_inquiry_content(data):
    """
    이메일 내용을 HTML과 텍스트 형식으로 포맷팅
    
    Args:
        data (dict): 검증된 폼 데이터
        
    Returns:
        tuple: (html_content: str, text_content: str)
    """
    current_time = datetime.now().strftime("%Y년 %m월 %d일 %H:%M:%S")
    
    # 데이터 이스케이프 처리
    school_name = escape(data.get('schoolName', ''))
    teacher_name = escape(data.get('teacherName', ''))
    phone = escape(data.get('phone', ''))
    email = escape(data.get('email', ''))
    inquiry = escape(data.get('inquiry', '문의 내용 없음'))
    
    # HTML 버전
    html_content = f"""
    <div style="font-family: 'Noto Sans KR', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0;">
            <h2 style="margin: 0; font-size: 24px;">📧 메가체육 문의 접수</h2>
            <p style="margin: 5px 0 0 0; opacity: 0.9;">새로운 문의가 접수되었습니다.</p>
        </div>
        
        <div style="background: #f8f9fa; padding: 20px; border: 1px solid #e9ecef;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px 12px; background: #fff; border: 1px solid #dee2e6; font-weight: bold; width: 120px;">학교명</td>
                    <td style="padding: 8px 12px; background: #fff; border: 1px solid #dee2e6;">{school_name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 12px; background: #f8f9fa; border: 1px solid #dee2e6; font-weight: bold;">담당자</td>
                    <td style="padding: 8px 12px; background: #f8f9fa; border: 1px solid #dee2e6;">{teacher_name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 12px; background: #fff; border: 1px solid #dee2e6; font-weight: bold;">연락처</td>
                    <td style="padding: 8px 12px; background: #fff; border: 1px solid #dee2e6;">{phone}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 12px; background: #f8f9fa; border: 1px solid #dee2e6; font-weight: bold;">이메일</td>
                    <td style="padding: 8px 12px; background: #f8f9fa; border: 1px solid #dee2e6;">{email}</td>
                </tr>
            </table>
            
            <div style="margin-top: 20px;">
                <h4 style="background: #667eea; color: white; padding: 10px; margin: 0 0 10px 0; border-radius: 5px;">📝 문의 내용</h4>
                <div style="background: white; padding: 15px; border: 1px solid #dee2e6; border-radius: 5px; white-space: pre-wrap; line-height: 1.6;">
{inquiry}
                </div>
            </div>
        </div>
        
        <div style="background: #6c757d; color: white; padding: 15px; text-align: center; border-radius: 0 0 10px 10px;">
            <p style="margin: 0; font-size: 14px;">📅 접수시간: {current_time}</p>
            <p style="margin: 5px 0 0 0; font-size: 12px; opacity: 0.8;">메가체육 자동 발송 시스템</p>
        </div>
    </div>
    """
    
    # 텍스트 버전
    text_content = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📧 메가체육 문의 접수
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏫 학교명: {school_name}
👤 담당자: {teacher_name}  
📞 연락처: {phone}
📧 이메일: {email}

📝 문의 내용:
{inquiry}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 접수시간: {current_time}
메가체육 자동 발송 시스템
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
    
    return html_content, text_content


def send_inquiry_email(data):
    """
    문의 이메일 전송
    
    Args:
        data (dict): 검증된 폼 데이터
        
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # 이메일 내용 포맷팅
        html_content, text_content = format_inquiry_content(data)
        
        # 이메일 제목
        subject = f"[메가체육] {data.get('schoolName')} - {data.get('teacherName')} 문의"
        
        # 발신자와 수신자
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [settings.EMAIL_HOST_USER]  # 자기 자신에게 보내기
        
        # 이메일 객체 생성 (HTML + 텍스트)
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=recipient_list,
        )
        
        # HTML 버전 첨부
        email.attach_alternative(html_content, "text/html")
        
        # 이메일 전송
        email.send()
        
        logger.info(f"문의 이메일 전송 성공: {data.get('email')} from {data.get('schoolName')}")
        return True, "문의가 성공적으로 접수되었습니다! 빠른 시일 내에 연락드리겠습니다."
        
    except Exception as e:
        logger.error(f"이메일 전송 실패: {str(e)}")
        
        # 구체적인 에러 메시지 반환
        if "Authentication failed" in str(e):
            return False, "이메일 인증에 실패했습니다. 관리자에게 문의해주세요."
        elif "Connection refused" in str(e):
            return False, "이메일 서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요."
        elif "timeout" in str(e).lower():
            return False, "이메일 전송 중 시간이 초과되었습니다. 다시 시도해주세요."
        else:
            return False, "이메일 전송 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."


@csrf_protect
@require_POST
def api_send_inquiry(request):
    """
    문의 이메일 전송 API 엔드포인트
    
    POST /physical_education/api/send-inquiry/
    
    Request Body:
    {
        "schoolName": "학교명",
        "teacherName": "담당자명",
        "phone": "010-1234-5678",
        "email": "email@school.com",
        "inquiry": "문의 내용"
    }
    
    Response:
    {
        "success": true/false,
        "message": "결과 메시지"
    }
    """
    try:
        # JSON 데이터 파싱
        data = json.loads(request.body)
        
        # 데이터 검증
        is_valid, errors = validate_email_data(data)
        
        if not is_valid:
            return JsonResponse({
                'success': False,
                'message': '입력 정보를 확인해주세요.',
                'errors': errors
            }, status=400)
        
        # 이메일 전송
        success, message = send_inquiry_email(data)
        
        if success:
            return JsonResponse({
                'success': True,
                'message': message
            })
        else:
            return JsonResponse({
                'success': False,
                'message': message
            }, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': '잘못된 요청 데이터입니다.'
        }, status=400)
        
    except Exception as e:
        logger.error(f"API 에러: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': '서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'
        }, status=500)