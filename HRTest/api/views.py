from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from .models import UserControl, UserActivity
from .serializers import UserControlSerializers
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)

class UserControlView(viewsets.ModelViewSet):
    queryset = UserControl.objects.all()
    serializer_class = UserControlSerializers

    @action(detail=False, methods=['post'], url_path='create_or_update')
    def create_or_update(self, request):
        try:
            telegram_id = request.data.get('tg_id')
            name = request.data.get('name')
            number_phone = request.data.get('number_phone')
            service = request.data.get('service')

            if not telegram_id or not name or not number_phone or not service:
                return Response({
                    'error': 'Все поля обязательны'
                }, status=status.HTTP_400_BAD_REQUEST)

            application = UserControl.objects.create(
                tg_id=telegram_id,
                name=name,
                number_phone=number_phone,
                service=service
            )

            serializer = self.get_serializer(application)
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Ошибка: {e}")
            return Response({
                'error': 'Ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='log_activity')
    def log_activity(self, request):
        try:
            user_id = request.data.get('user_id')
            action = request.data.get('action')

            if not user_id or not action:
                return Response({
                    'error': 'user_id и action обязательны'
                }, status=status.HTTP_400_BAD_REQUEST)

            UserActivity.objects.create(
                user_id=user_id,
                action=action
            )

            return Response({
                'success': True
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Ошибка логирования активности: {e}")
            return Response({
                'error': 'Ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='daily_stats')
    def daily_stats(self, request):
        try:
            yesterday = timezone.now() - timedelta(days=1)
            
            unique_users = UserActivity.objects.filter(
                timestamp__gte=yesterday
            ).values('user_id').distinct().count()
            
            return Response({
                'unique_users_24h': unique_users,
                'period': 'last_24_hours'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Ошибка статистики: {e}")
            return Response({
                'error': 'Ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        