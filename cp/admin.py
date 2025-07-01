# cp/admin.py
from django.contrib import admin
from .models import Contents_Template

@admin.register(Contents_Template)
class ContentsAdmin(admin.ModelAdmin):
    list_display = ['title', 'content_type', 'created_by', 'created_at', 'is_active','is_public']
    list_filter = ['content_type', 'is_active', 'created_at','is_public']
    search_fields = ['title', 'page','is_public']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('content_category','content_type', 'title', 'is_active')
        }),
        ('콘텐츠', {
            'fields': ('page', 'answer')
        }),
        ('메타데이터', {
            'fields': ('meta_data', 'tags'),
            'classes': ('collapse',)
        }),
        ('시스템 정보', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )