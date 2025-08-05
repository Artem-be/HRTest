from django.db import models

class UserControl(models.Model):
    tg_id = models.BigIntegerField()
    name = models.CharField(max_length=100)
    number_phone = models.CharField(max_length=100)
    service = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'UserControl'
        verbose_name_plural = 'UserControls'
        indexes = [
            models.Index(fields=['tg_id']),
            models.Index(fields=['created_at']),
        ]

class UserActivity(models.Model):
    user_id = models.BigIntegerField()
    action = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'UserActivity'
        verbose_name_plural = 'UserActivities'
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['timestamp']),
        ]