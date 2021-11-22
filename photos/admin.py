from django.contrib import admin
from photos.models import Photo


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('user', 'file', 'status', 'has_deleted', 'created_at')
    list_filter = ('status', 'has_deleted')
