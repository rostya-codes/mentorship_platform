from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.http import Http404
from django.shortcuts import redirect, render
from django.views import View

from mentorship_platform.tasks import send_booking_confirmation_email
from schedule.forms import CreateSlotForm, UpdateSlotForm
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

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_mentor:
            return render(request, '403.html', status=403)

        slots = Slot.objects.filter(mentor=request.user).order_by('date', 'time')
        return render(request, 'schedule/mentor-slots.html', {'slots': slots})


class CreateSlotView(View):
    """ Створює слот для ментора """

    def post(self, request):
        if not request.user.is_authenticated or not request.user.is_mentor:
            return render(request, '403.html', status=403)

        form = CreateSlotForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.mentor = request.user
            slot.save()
            return redirect('mentor-slots')
        return render(request, 'schedule/create-slot.html', {'form': form})

    def get(self, request, *args, **kwargs):
        form = CreateSlotForm()
        return render(request, 'schedule/create-slot.html', {'form': form})


class UpdateSlotView(View):

    def post(self, request, slot_id):
        slot = Slot.objects.get(pk=slot_id)
        form = UpdateSlotForm(request.POST, instance=slot)
        if form.is_valid():
            form.save()
            return redirect('mentor-slots')
        return render(request, 'schedule/update-slot.html', {'form': form})

    def get(self, request, slot_id, *args, **kwargs):
        slot = Slot.objects.get(pk=slot_id)
        form = UpdateSlotForm(instance=slot)
        return render(request, 'schedule/update-slot.html', {'form': form})


class DeleteSlotView(View):

    def post(self, request, slot_id):
        try:
            slot = Slot.objects.get(pk=slot_id)
        except Slot.DoesNotExist:
            raise Http404('Slot not found or you don\'t have permission')
        slot.delete()
        return redirect('mentor-slots')


