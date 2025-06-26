from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AssetViewSet, NotificationViewSet, ViolationViewSet, run_checks

router = DefaultRouter()
router.register(r'assets', AssetViewSet)
router.register(r'notifications', NotificationViewSet)
router.register(r'violations', ViolationViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('run-checks/', run_checks, name='run-checks'),
]