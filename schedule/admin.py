from django.contrib import admin

from schedule.models import BookingLog, Slot

admin.site.register(Slot)
admin.site.register(BookingLog)
