from django.contrib import admin
from .models import UserControl, UserActivity

@admin.register(UserControl)
class UserControlAdmin(admin.ModelAdmin):
    list_display = ('tg_id', 'name', 'number_phone', 'service', 'created_at')
    list_filter = ('service', 'created_at')
    search_fields = ('name', 'number_phone', 'tg_id')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('tg_id', 'name', 'number_phone', 'service')
        }),
        ('Метаданные', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'action', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('user_id', 'action')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    
    fieldsets = (
        ('Активность', {
            'fields': ('user_id', 'action')
        }),
        ('Время', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        }),
    )
