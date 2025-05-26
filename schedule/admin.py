from django.contrib import admin

from schedule.models import Slot, BookingLog

admin.site.register(Slot)
admin.site.register(BookingLog)
