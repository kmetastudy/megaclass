from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from teacher.decorators import teacher_required


@login_required
@teacher_required
def teacher_dashboard(request):
    """체육 교사 대시보드 뷰"""
    context = {
        "user": request.user,
    }
    return render(request, "physical_education/teachers/dashboard.html", context)
