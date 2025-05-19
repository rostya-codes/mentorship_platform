from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.views import View

from reviews.forms import LeaveReviewForm
from reviews.models import Review
from schedule.models import Slot

User = get_user_model()


class MentorProfileView(View):
    def get(self, request, mentor_id, *args, **kwargs):
        mentor = User.objects.get(pk=mentor_id)
        reviews = Review.objects.filter(mentor=mentor)
        return render(
            request,
            'reviews/mentor-profile.html',
            {'mentor': mentor, 'reviews': reviews},
        )


class LeaveReviewView(View):
    def post(self, request, booking_id):
        booking = Slot.objects.get(pk=booking_id)
        mentor = booking.mentor
        form = LeaveReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.mentor = mentor
            review.user = request.user
            review.save()
            return redirect('my-bookings')
        return render(request, 'reviews/leave-review.html', {'form': form})
