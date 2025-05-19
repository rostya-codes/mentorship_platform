from datetime import datetime

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import redirect, render
from django.views import View
from django.utils import timezone

from mentorship_platform.tasks import send_booking_confirmation_email
from schedule.models import Slot

User = get_user_model()


class SlotListView(View):
    """ Відображає список усіх доступних слотів для бронювання """

    def get(self, request, *args, **kwargs):
        slots = Slot.objects.filter(is_booked=False)
        if not slots:
            # Можна додати повідомлення, що немає доступних слотів
            messages.info(request, "No available slots at the moment.", extra_tags='info')
        return render(request, 'schedule/slots-list.html', {'slots': slots})


@method_decorator(login_required, name='dispatch')
class BookSlotView(View):
    """ Обробляє бронювання слоту користувачем """

    def get(self, request, slot_id, *args, **kwargs):
        slot = Slot.objects.get(pk=slot_id)
        user = request.user
        slot.user = user
        slot.is_booked = True
        slot.save()
        message = (
            f"Hi {request.user.first_name},\n\n"
            f"Your slot with mentor {slot.mentor.get_full_name()} "
            f"on {slot.date.strftime('%A, %B %d, %Y')} at {slot.time.strftime('%H:%M')} has been successfully booked.\n\n"
            "If you have any questions, feel free to contact us.\n\n"
            "Thank you for using our mentorship platform!"
        )
        send_booking_confirmation_email.delay(
            user.email,
            user.first_name,
            slot.mentor.get_full_name(),
            slot.date.isoformat(),
            slot.time.strftime('%H:%M')
        )
        messages.success(request, 'Slot booked.', extra_tags='success')
        return redirect('my-bookings')


@method_decorator(login_required, name='dispatch')
class CancelBookingView(View):
    """ Дозволяє користувачу скасувати раніше зроблене бронювання """

    def get(self, request, *args, **kwargs):
        booking = Slot.objects.get(user=request.user)
        booking.user = None
        booking.is_booked = False
        booking.save()
        messages.success(request, 'Slot canceled.', extra_tags='success')
        return redirect('my-bookings')


@method_decorator(login_required, name='dispatch')
class MyBookingsView(View):
    """ Відображає список консультацій, які користувач забронював """

    def get(self, request, *args, **kwargs):
        bookings = Slot.objects.filter(user=request.user).order_by('-date', '-time')
        now = timezone.now()
        for booking in bookings:
            booking.slot_datetime = timezone.make_aware(datetime.combine(booking.date, booking.time))
        return render(request, 'schedule/my-bookings.html', {'bookings': bookings, 'now': now})
