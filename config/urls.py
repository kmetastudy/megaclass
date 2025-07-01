from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect, render

def root_redirect(request):
    """루트 URL에서 사용자 타입에 따라 리다이렉트"""
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    
    if hasattr(request.user, 'teacher'):
        return redirect('teacher:dashboard')
    elif hasattr(request.user, 'student'):
        return redirect('student:dashboard')
    else:
        return redirect('accounts:profile')
    
def index(request):
    return render(request,'landing.html')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    # path('', root_redirect, name='root'),
    path('accounts/', include('accounts.urls')),
    path('rolling/', include('rolling.urls')),
    path('teacher/', include('teacher.urls')),
    path('student/', include('student.urls')),
    path('health_habit/', include('app_home.urls')),
    path('cp/', include('new_cp.urls')),
    path('agent/', include('super_agent.urls')),
    path('ncs/', include('ncs.urls')),

    ]
#     path('cp/', include('cp.urls')),
# ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])