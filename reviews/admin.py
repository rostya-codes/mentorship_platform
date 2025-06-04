from django.contrib import admin

from reviews.models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'rating',
        'short_comment',
        'mentor',
        'user',
        'slot',
        'created_at',
    )
    readonly_fields = (
        'id',
    )
    search_fields = (
        'mentor__username',
        'user__username',
        'slot__id',
        'comment',
    )
    list_filter = (
        'rating',
        'mentor',
        'user',
        'slot',
        'created_at',
    )
    ordering = ('-created_at',)

    def short_comment(self, obj):
        return obj.comment[:30] + ('...' if len(obj.comment) > 30 else '')  # obj - текущий объект модели (Review)
    short_comment.short_description = 'Comment'
