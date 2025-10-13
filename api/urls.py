from django.urls import include, path
from points.urls import api_patterns as points_api_patterns

urlpatterns = [
    path("points/", include(points_api_patterns)),
]
