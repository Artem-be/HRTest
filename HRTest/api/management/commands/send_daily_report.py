from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import requests
import logging
import os

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Отправка ежедневного отчёта администратору'

    def add_arguments(self, parser):
        parser.add_argument(
            '--bot-token',
            type=str,
            help='Telegram Bot Token'
        )
        parser.add_argument(
            '--admin-id',
            type=int,
            help='Admin Telegram ID'
        )

    def handle(self, *args, **options):
        try:
            from ..models import UserActivity
            
            yesterday = timezone.now() - timedelta(days=1)
            
            unique_users = UserActivity.objects.filter(
                timestamp__gte=yesterday
            ).values('user_id').distinct().count()
            
            report_text = f"📊 Ежедневный отчёт\n\nЗа прошедшие сутки ботом воспользовались {unique_users} пользователей"
            
            bot_token = options['bot_token'] or os.getenv('BOT_TOKEN')
            admin_id = options['admin_id'] or int(os.getenv('ADMIN_ID', '123456789'))
            
            if not bot_token:
                self.stdout.write(
                    self.style.ERROR('Не указан BOT_TOKEN')
                )
                return
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                'chat_id': admin_id,
                'text': report_text
            }
            
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Отчёт отправлен: {unique_users} пользователей')
                )
                logger.info(f"Ежедневный отчёт отправлен: {unique_users} пользователей")
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Ошибка отправки: {response.status_code}')
                )
                logger.error(f"Ошибка отправки отчёта: {response.status_code}")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка: {e}')
            )
            logger.error(f"Ошибка отправки отчёта: {e}") 