from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'session_key', 'profile_type', 'market_preference', 'created_at']
    list_filter = ['profile_type', 'market_preference', 'created_at']
    search_fields = ['session_key', 'user__username']
    readonly_fields = ['created_at', 'updated_at']