from django.contrib import admin
from newsfeeds.models import NewsFeed


@admin.register(NewsFeed)
class NewsFeedAdmin(admin.ModelAdmin):
    list_display = ('user', 'tweet', 'created_at')
    date_hierarchy = 'created_at'
