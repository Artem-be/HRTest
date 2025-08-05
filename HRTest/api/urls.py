from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'usercontrol', views.UserControlView, basename='usercontrol')

urlpatterns = [
    path('', include(router.urls))
]
