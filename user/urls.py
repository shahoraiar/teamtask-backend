from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import RegisterViewSet, ProfileViewSet, CompanyViewSet, TeamViewSet, TaskViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r'register', RegisterViewSet, basename='register')
router.register(r'profile', ProfileViewSet, basename='profile')
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'teams', TeamViewSet, basename='team')
router.register(r'tasks', TaskViewSet, basename='task')

urlpatterns = [
    path('', include(router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
