from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

from django.contrib.auth.models import User
from .forms import TeacherRegistrationForm
from .models import Teacher, School, Student

from django.views.decorators.http import require_POST
from django.db import transaction
import logging

from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.middleware.csrf import get_token

# 로거 설정
logger = logging.getLogger(__name__)

@ensure_csrf_cookie  # CSRF 쿠키가 확실히 설정되도록 보장
def login_view(request):
    """
    개선된 UI/UX를 지원하는 로그인 처리 뷰 (POST 데이터 디버깅 강화)
    """
    
    # 이미 로그인한 사용자는 적절한 대시보드로 리다이렉트
    if request.user.is_authenticated:
        if hasattr(request.user, 'student'):
            return redirect('student:dashboard')
        elif hasattr(request.user, 'teacher'):
            return redirect('teacher:dashboard')
        else:
            return redirect('admin:index')
    
    # GET 요청 시, 학교 목록을 템플릿에 전달
    schools = School.objects.all()
    context = {'schools': schools}

    if request.method == 'POST':
        # ============ 디버깅 정보 출력 ============
        print("="*50)
        print("POST REQUEST DEBUG INFO")
        print("="*50)
        print(f"Content-Type: {request.content_type}")
        print(f"POST data keys: {list(request.POST.keys())}")
        print(f"POST data: {dict(request.POST)}")
        print(f"Raw POST body (first 200 chars): {request.body[:200]}")
        print("="*50)
        
        # POST 데이터에서 값 추출
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        school_code = request.POST.get('school_code', '').strip()
        
        # 추출된 값들 디버깅
        print(f"Extracted username: '{username}' (length: {len(username)})")
        print(f"Extracted password: '{'*' * len(password)}' (length: {len(password)})")
        print(f"Extracted school_code: '{school_code}' (length: {len(school_code)})")
        print("="*50)

        # 입력값 기본 검증 (더 상세한 체크)
        if not username:
            print("ERROR: Username is empty or None")
            messages.error(request, '학번(사번)을 입력해주세요.')
            return render(request, 'accounts/login.html', context)
            
        if not password:
            print("ERROR: Password is empty or None")
            messages.error(request, '비밀번호를 입력해주세요.')
            return render(request, 'accounts/login.html', context)

        print("✅ Both username and password are provided")
        user = None

        # ID가 숫자로 시작하면 학생으로 처리
        if username.isdigit():
            print(f"Processing as STUDENT login: {username}")
            if school_code:
                try:
                    selected_school = School.objects.get(code=school_code)
                    full_username = f"{selected_school.code}_{username}"
                    print(f"Trying authentication with full_username: {full_username}")
                    user = authenticate(request, username=full_username, password=password)
                    
                    if user is None:
                        print(f"❌ Authentication failed for: {full_username}")
                        messages.error(request, '학번, 비밀번호 또는 선택한 학교를 다시 확인해주세요.')
                        return render(request, 'accounts/login.html', context)
                    else:
                        print(f"✅ Authentication successful for: {full_username}")
                        
                except School.DoesNotExist:
                    print(f"❌ School not found with code: {school_code}")
                    messages.error(request, '선택한 학교를 찾을 수 없습니다.')
                    return render(request, 'accounts/login.html', context)
            else:
                print("No school selected, trying all schools...")
                # 학교가 선택되지 않은 경우 모든 학교에서 찾기 시도
                for school in schools:
                    full_username = f"{school.code}_{username}"
                    print(f"Trying: {full_username}")
                    user = authenticate(request, username=full_username, password=password)
                    if user is not None:
                        print(f"✅ Found user in school: {school.name}")
                        break
                
                if user is None:
                    print("❌ Student not found in any school")
                    messages.error(request, '학번 또는 비밀번호가 올바르지 않습니다. 학교를 선택하면 더 정확한 로그인이 가능합니다.')
                    return render(request, 'accounts/login.html', context)
        
        # ID가 숫자로 시작하지 않으면 교사/관리자로 처리
        else:
            print(f"Processing as TEACHER/ADMIN login: {username}")
            user = authenticate(request, username=username, password=password)
            if user is None:
                print(f"❌ Teacher/Admin authentication failed for: {username}")
                messages.error(request, '사번 또는 비밀번호가 올바르지 않습니다.')
                return render(request, 'accounts/login.html', context)
            else:
                print(f"✅ Teacher/Admin authentication successful for: {username}")

        # 인증 성공 시 로그인 처리
        if user is not None:
            login(request, user)
            print(f"✅ User logged in successfully: {user.username}")
            
            # 성공 메시지에 학교 정보 추가 (학생인 경우)
            if hasattr(user, 'student'):
                school_name = user.student.school_class.school.name
                messages.success(request, f"{school_name} {user.get_full_name()}님, 환영합니다!")
            else:
                messages.success(request, f"{user.get_full_name()}님, 환영합니다!")
            
            # next URL이 있으면 해당 URL로, 없으면 사용자 타입에 따라 리다이렉트
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            
            # 사용자 타입에 따라 적절한 대시보드로 리다이렉트
            if hasattr(user, 'student'):
                return redirect('student:dashboard')
            elif hasattr(user, 'teacher'):
                return redirect('teacher:dashboard')
            else:
                return redirect('admin:index')

    return render(request, 'accounts/login.html', context)

def login_view_0619(request):
    """
    개선된 UI/UX를 지원하는 로그인 처리 뷰
    - ID가 숫자로 시작하면 학생으로 간주하고, 자동으로 모든 학교에서 매칭을 시도합니다.
    """
    # 이미 로그인한 사용자는 적절한 대시보드로 리다이렉트
    if request.user.is_authenticated:
        if hasattr(request.user, 'student'):
            return redirect('student:dashboard')
        elif hasattr(request.user, 'teacher'):
            return redirect('teacher:dashboard')
        else:
            return redirect('admin:index')
    
    # GET 요청 시, 학교 목록을 템플릿에 전달
    schools = School.objects.all()
    context = {'schools': schools}

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        # 입력값 기본 검증
        if not username or not password:
            messages.error(request, '학번(사번)과 비밀번호를 모두 입력해주세요.')
            return render(request, 'accounts/login.html', context)

        user = None

        # ID가 숫자로 시작하면 학생으로 처리
        if username.isdigit():
            # 모든 학교에서 학생 계정 찾기 시도
            for school in schools:
                full_username = f"{school.code}_{username}"
                user = authenticate(request, username=full_username, password=password)
                if user is not None:
                    break
            
            # 학생을 찾지 못한 경우
            if user is None:
                messages.error(request, '학번 또는 비밀번호가 올바르지 않습니다.')
                return render(request, 'accounts/login.html', context)
        
        # ID가 숫자로 시작하지 않으면 교사/관리자로 처리
        else:
            user = authenticate(request, username=username, password=password)
            if user is None:
                messages.error(request, '사번 또는 비밀번호가 올바르지 않습니다.')
                return render(request, 'accounts/login.html', context)

        # 인증 성공 시 로그인 처리
        if user is not None:
            login(request, user)
            messages.success(request, f"{user.get_full_name()}님, 환영합니다!")
            
            # next URL이 있으면 해당 URL로, 없으면 사용자 타입에 따라 리다이렉트
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            
            # 사용자 타입에 따라 적절한 대시보드로 리다이렉트
            if hasattr(user, 'student'):
                return redirect('student:dashboard')
            elif hasattr(user, 'teacher'):
                return redirect('teacher:dashboard')
            else:
                return redirect('admin:index')

    return render(request, 'accounts/login.html', context)

def login_view_0617(request):
    """
    개선된 UI/UX를 지원하는 로그인 처리 뷰
    - ID가 숫자로 시작하면 학생으로 간주하고, 학교 선택을 필수로 요구합니다.
    """
    # 이미 로그인한 사용자는 대시보드로 리다이렉트
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    # GET 요청 시, 학교 목록을 템플릿에 전달
    schools = School.objects.all()
    context = {'schools': schools}

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        school_code = request.POST.get('school_code')

        # 입력값 기본 검증
        if not username or not password:
            messages.error(request, '학번(사번)과 비밀번호를 모두 입력해주세요.')
            return render(request, 'accounts/login.html', context)

        full_username = username
        user = None

        # ID가 숫자로 시작하면 학생으로 처리
        if username.isdigit():
            if not school_code:
                messages.error(request, '학생은 반드시 학교를 선택해야 합니다.')
                return render(request, 'accounts/login.html', context)
            
            # Django User 모델의 username 형식에 맞게 조합 ('학교코드_학번')
            full_username = f"{school_code}_{username}"
            user = authenticate(request, username=full_username, password=password)
        
        # ID가 숫자로 시작하지 않으면 교사/관리자로 처리
        else:
            user = authenticate(request, username=full_username, password=password)

        # 인증 결과 처리
        if user is not None:
            login(request, user)
            messages.success(request, f"{user.get_full_name()}님, 환영합니다!")
            
            # 로그인 후 대시보드로 리다이렉트 (dashboard URL이 자동으로 적절한 곳으로 보냄)
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, '입력하신 정보가 올바르지 않거나, 소속 학교를 다시 확인해주세요.')

    return render(request, 'accounts/login.html', context)


def login_view_0618(request):
    """
    개선된 UI/UX를 지원하는 로그인 처리 뷰
    - ID가 숫자로 시작하면 학생으로 간주하고, 학교 선택을 필수로 요구합니다.
    """
    # GET 요청 시, 학교 목록을 템플릿에 전달
    schools = School.objects.all()
    context = {'schools': schools}

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        school_code = request.POST.get('school_code')

        # 입력값 기본 검증
        if not username or not password:
            messages.error(request, '학번(사번)과 비밀번호를 모두 입력해주세요.')
            return render(request, 'accounts/login.html', context)

        full_username = username
        user = None

        # ID가 숫자로 시작하면 학생으로 처리
        if username.isdigit():
            if not school_code:
                messages.error(request, '학생은 반드시 학교를 선택해야 합니다.')
                return render(request, 'accounts/login.html', context)
            
            # Django User 모델의 username 형식에 맞게 조합 ('학교코드_학번')
            full_username = f"{school_code}_{username}"
            user = authenticate(request, username=full_username, password=password)
        
        # ID가 숫자로 시작하지 않으면 교사/관리자로 처리
        else:
            user = authenticate(request, username=full_username, password=password)

        # 인증 결과 처리
        if user is not None:
            login(request, user)
            messages.success(request, f"{user.get_full_name()}님, 환영합니다!")
            
            if hasattr(user, 'student'):
                return redirect('student:dashboard')
            elif hasattr(user, 'teacher'):
                return redirect('teacher:dashboard')
            else: # Superuser 등
                return redirect('admin:index')
        else:
            messages.error(request, '입력하신 정보가 올바르지 않거나, 소속 학교를 다시 확인해주세요.')

    return render(request, 'accounts/login.html', context)

def login_view_0607(request):
    """학번/사번으로 로그인 처리"""
    # 템플릿에서 학교 목록을 뿌려주기 위해 QuerySet 전달
    schools = School.objects.all()
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        school_code = request.POST.get('school_code')  # 학교 선택
        
        # 학번으로 로그인한 경우 (username이 숫자로 시작)
        if username and username[0].isdigit():
            # 학교 코드가 선택되었으면 학번 앞에 붙이기
            if school_code:
                full_username = f"{school_code}_{username}"
            else:
                # 학교가 선택되지 않았으면 모든 학교에서 시도
                for school in schools:
                    full_username = f"{school.code}_{username}"
                    user = authenticate(request, username=full_username, password=password)
                    if user is not None:
                        break
                else:
                    # 모든 학교에서 찾지 못한 경우
                    messages.error(request, '학번 또는 비밀번호가 올바르지 않습니다.')
                    return render(request, 'accounts/login.html', {'schools': schools})
        else:
            # 교사/관리자는 그대로 사용
            full_username = username
        
        # 인증 시도
        user = authenticate(request, username=full_username, password=password)
        
        if user is not None:
            login(request, user)
            
            # 학생인 경우
            if hasattr(user, 'student'):
                return redirect('student:dashboard')
            # 교사인 경우
            elif hasattr(user, 'teacher'):
                return redirect('teacher:dashboard')
            # 관리자인 경우
            else:
                return redirect('admin:index')
        else:
            messages.error(request, '아이디 또는 비밀번호가 올바르지 않습니다.')
    
    return render(request, 'accounts/login.html', {'schools': schools})

def login_view_0603(request):
    """학번/사번으로 로그인 처리"""
     # 템플릿에서 학교 목록을 뿌려주기 위해 QuerySet 전달
    schools = School.objects.all()
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # 학번으로 로그인한 경우 (username이 숫자로 시작)
            if username[0].isdigit():
                # 학생 확인
                if hasattr(user, 'student'):
                    return redirect('student:dashboard')
                else:
                    messages.error(request, '학생 정보가 없습니다.')
                    return redirect('accounts:login')
            else:
                # 교사/관리자
                if hasattr(user, 'teacher'):
                    return redirect('teacher:dashboard')
                else:
                    return redirect('admin:index')
        else:
            messages.error(request, '아이디 또는 비밀번호가 올바르지 않습니다.')
    
    return render(request, 'accounts/login.html',{'schools':schools})

def login_view_0602(request):
    """로그인 페이지 (학교 선택 포함)"""
    if request.user.is_authenticated:
        return redirect('/')

    # 템플릿에서 학교 목록을 뿌려주기 위해 QuerySet 전달
    schools = School.objects.all()

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        school_id = request.POST.get('school')  # select에서 선택된 학교 id

        user = authenticate(request, username=username, password=password)
        if user is not None:
            # 학교 일치 검사
            if hasattr(user, 'teacher'):
                # user가 교사이면 user.teacher.school.id 검사
                if str(user.teacher.school.id) != str(school_id):
                    messages.error(request, '학교 정보가 일치하지 않습니다.')
                    return redirect('accounts:login')
                
                login(request, user)
                return redirect('teacher:dashboard')

            elif hasattr(user, 'student'):
                # user가 학생이면 user.student.school_class.school.id 검사
                if str(user.student.school_class.school.id) != str(school_id):
                    messages.error(request, '학교 정보가 일치하지 않습니다.')
                    return redirect('accounts:login')
                
                login(request, user)
                return redirect('student:dashboard')
            
            else:
                # 교사, 학생 둘 다 해당 안 되는 경우(관리자나 기타)
                login(request, user)
                return redirect('accounts:profile')
        else:
            messages.error(request, '잘못된 사용자명 또는 비밀번호입니다.')

    return render(request, 'accounts/login.html', {
        'schools': schools
    })

@login_required
def logout_view(request):
    """로그아웃"""
    logout(request)
    messages.success(request, '로그아웃되었습니다.')
    return redirect('accounts:login')

@login_required
def profile_view(request):
    """프로필 페이지"""
    context = {
        'user': request.user
    }
    
    if hasattr(request.user, 'teacher'):
        context['profile'] = request.user.teacher
        context['user_type'] = 'teacher'
    elif hasattr(request.user, 'student'):
        context['profile'] = request.user.student
        context['user_type'] = 'student'
    
    return render(request, 'accounts/profile.html', context)

# API Views (기존 JavaScript와 호환성을 위해)
@csrf_exempt
@require_http_methods(["POST"])
def api_login(request):
    """API 로그인"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            user_data = {
                'id': user.id,
                'username': user.username,
                'name': user.get_full_name(),
                'email': user.email,
            }
            
            if hasattr(user, 'teacher'):
                user_data['type'] = 'teacher'
                user_data['profile'] = user.teacher.to_dict()
            elif hasattr(user, 'student'):
                user_data['type'] = 'student'
                user_data['profile'] = user.student.to_dict()
            
            return JsonResponse({
                'success': True,
                'user': user_data
            })
        else:
            return JsonResponse({'error': '잘못된 사용자명 또는 비밀번호입니다.'}, status=400)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@require_http_methods(["POST"])
def api_logout(request):
    """API 로그아웃"""
    logout(request)
    return JsonResponse({'success': True})

@require_http_methods(["GET"])
def api_profile(request):
    """API 프로필 조회"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    user_data = {
        'id': request.user.id,
        'username': request.user.username,
        'name': request.user.get_full_name(),
        'email': request.user.email,
    }
    
    if hasattr(request.user, 'teacher'):
        user_data['type'] = 'teacher'
        user_data['profile'] = request.user.teacher.to_dict()
    elif hasattr(request.user, 'student'):
        user_data['type'] = 'student'
        user_data['profile'] = request.user.student.to_dict()
    
    return JsonResponse({'user': user_data})


def teacher_register_view(request):
    """
    교사 회원가입 페이지를 렌더링합니다.
    (실제 데이터 처리는 api_teacher_register 뷰에서 AJAX로 수행)
    """
    # 템플릿에 학교 목록을 전달하기 위해 form 인스턴스 생성
    form = TeacherRegistrationForm()
    return render(request, 'accounts/teacher_register.html', {'form': form})


@require_POST
@transaction.atomic # DB 작업을 트랜잭션으로 묶어 데이터 일관성 보장
def api_teacher_register(request):
    """
    AJAX 요청을 통해 교사 회원가입을 처리하는 API 뷰.
    """
    try:
        data = json.loads(request.body)
        form = TeacherRegistrationForm(data)

        if form.is_valid():
            # UserCreationForm을 상속받았으므로, form.save()가 User를 생성
            user = form.save(commit=False)
            
            # 폼 데이터에서 User 모델 필드 채우기
            user.first_name = form.cleaned_data.get('first_name', '')
            user.last_name = form.cleaned_data.get('last_name', '')
            user.email = form.cleaned_data.get('email', '')
            user.save()

            # Teacher 모델 생성
            Teacher.objects.create(
                user=user,
                school=form.cleaned_data['school'],
                employee_id=form.cleaned_data['employee_id'],
                phone=form.cleaned_data.get('phone', '')
            )
            
            return JsonResponse({'status': 'success', 'message': '회원가입이 완료되었습니다. 로그인 페이지로 이동합니다.'})
        else:
            # 폼 유효성 검증 실패 시, 에러 정보를 JSON으로 반환
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': '잘못된 형식의 요청입니다.'}, status=400)
    except Exception as e:
        # 기타 예상치 못한 에러 처리
        return JsonResponse({'status': 'error', 'message': f'서버 오류가 발생했습니다: {str(e)}'}, status=500)









def teacher_register_view_0607(request):
    """교사 회원가입"""
    if request.method == 'POST':
        form = TeacherRegistrationForm(request.POST)
        if form.is_valid():
            # UserCreationForm을 상속받아, user 인스턴스를 먼저 저장
            user = form.save(commit=False)
            
            # 폼에 추가한 name / email 등을 User에 저장
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()  # DB 저장 (User 생성)
            
            # Teacher 모델 생성
            Teacher.objects.create(
                user=user,
                school=form.cleaned_data['school'],
                employee_id=form.cleaned_data['employee_id'],
                phone=form.cleaned_data['phone']
            )
            
            messages.success(request, '교사 계정이 성공적으로 생성되었습니다. 로그인해주세요.')
            return redirect('accounts:login')
        else:
            messages.error(request, '입력 내용을 다시 확인해주세요.')
    else:
        form = TeacherRegistrationForm()

    return render(request, 'accounts/teacher_register.html', {'form': form})