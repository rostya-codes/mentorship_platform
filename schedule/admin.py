from django.contrib import admin

from schedule.models import BookingLog, Slot

admin.site.register(BookingLog)


@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display = ("id", "mentor", "date", "time", "user", "is_booked", "get_review_link")
    readonly_fields = ('get_review_link',)
