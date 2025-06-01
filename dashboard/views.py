from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView

from schedule.models import Slot

from .forms import CreateSlotForm, UpdateSlotForm

User = get_user_model()


class MentorSlotsView(View):
    """ Відображає список слотів, створених ментором, з інформацією про бронювання """

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_mentor:
            return render(request, '403.html', status=403)

        slots = Slot.objects.filter(mentor=request.user).order_by('date', 'time')
        return render(request, 'dashboard/mentor-slots.html', {'slots': slots})


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
        return render(request, 'dashboard/create-slot.html', {'form': form})

    def get(self, request, *args, **kwargs):
        form = CreateSlotForm()
        return render(request, 'dashboard/create-slot.html', {'form': form})


class UpdateSlotView(View):

    def post(self, request, slot_id):
        slot = Slot.objects.get(pk=slot_id)
        form = UpdateSlotForm(request.POST, instance=slot)
        if form.is_valid():
            form.save()
            return redirect('mentor-slots')
        return render(request, 'dashboard/update-slot.html', {'form': form})

    def get(self, request, slot_id, *args, **kwargs):
        slot = Slot.objects.get(pk=slot_id)
        form = UpdateSlotForm(instance=slot)
        return render(request, 'dashboard/update-slot.html', {'form': form})


class DeleteSlotView(View):

    def post(self, request, slot_id):
        try:
            slot = Slot.objects.get(pk=slot_id)
        except Slot.DoesNotExist:
            raise Http404('Slot not found or you don\'t have permission')
        slot.delete()
        return redirect('mentor-slots')


@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(lambda u: u.is_staff), name='dispatch')  # тільки для адміністраторів
class DashboardView(View):
    """ Statistics displaying """

    def get(self, request):
        total_users = User.objects.count()
        total_mentors = User.objects.filter(is_mentor=True).count()
        total_slots = Slot.objects.count()
        booked_slots = Slot.objects.filter(is_booked=True).count()
        free_slots = Slot.objects.filter(is_booked=False).count()

        context = {
            'total_users': total_users,
            'total_mentors': total_mentors,
            'total_slots': total_slots,
            'booked_slots': booked_slots,
            'free_slots': free_slots,
        }
        return render(request, 'dashboard/dashboard.html', context)


@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(lambda u: u.is_staff), name='dispatch')  # тільки для адміністраторів
class UsersList(ListView):
    template_name = 'dashboard/users-list.html'
    model = User
    context_object_name = 'users'


@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(lambda u: u.is_staff), name='dispatch')  # тільки для адміністраторів
class BanUser(View):
    def get(self, request, user_id, *args, **kwargs):
        user = User.objects.get(pk=user_id)
        user.is_active = False
        user.save()
        return redirect('users-list')


@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(lambda u: u.is_staff), name='dispatch')  # тільки для адміністраторів
class UnbanUser(View):
    def get(self, request, user_id, *args, **kwargs):
        user = User.objects.get(pk=user_id)
        user.is_active = True
        user.blocked_until = None
        user.last_unblocked = timezone.now()
        user.save()
        return redirect('users-list')
