from functools import wraps

from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages


def student_required(view_func):
    """학생 권한 필요한 뷰 데코레이터"""

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not hasattr(request.user, "student"):
            messages.error(request, "학생만 접근 가능합니다.")
            return redirect("accounts:login")

        return view_func(request, *args, **kwargs)

    return login_required(_wrapped_view)


def teacher_required(view_func):
    """교사 권한 필요한 뷰 데코레이터"""

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # 로그인 확인은 @login_required 데코레이터가 처리하므로 여기서는 생략
        if not hasattr(request.user, "teacher"):
            messages.error(request, "교사만 접근 가능합니다.")
            return redirect("accounts:login")
        return view_func(request, *args, **kwargs)

    return login_required(_wrapped_view)
