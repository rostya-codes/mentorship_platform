from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View
from pipenv.cli.options import keep_outdated_option

from schedule.models import Slot


class SlotListView(View):
    """ Відображає список усіх доступних слотів для бронювання """

    def get(self, request, *args, **kwargs):
        slots = Slot.objects.filter(is_booked=False)
        if not slots:
            # Можна додати повідомлення, що немає доступних слотів
            messages.info(request, "No available slots at the moment.", extra_tags='info')
        return render(request, 'schedule/slots-list.html', {'slots': slots})


class BookSlotView(View):
    """ Обробляє бронювання слоту користувачем """

    def get(self, request, slot_id, *args, **kwargs):
        slot = Slot.objects.get(pk=slot_id)
        slot.user = request.user
        slot.is_booked = True
        slot.save()
        messages.success(request, 'Slot booked.', extra_tags='success')
        return redirect('my-bookings')


class CancelBookingView(View):
    """ Дозволяє користувачу скасувати раніше зроблене бронювання """

    def get(self, request, *args, **kwargs):
        booking = Slot.objects.get(user=request.user)
        booking.user = None
        booking.is_booked = False
        booking.save()
        messages.success(request, 'Slot canceled.', extra_tags='success')
        return redirect('my-bookings')


class MyBookingsView(View):
    """ Відображає список консультацій, які користувач забронював """

    def get(self, request, *args, **kwargs):
        bookings = Slot.objects.filter(user=request.user)
        return render(request, 'schedule/my-bookings.html', {'bookings': bookings})


class MentorSlotsView(View):
    """ Відображає список слотів, створених ментором, з інформацією про бронювання """

    pass
