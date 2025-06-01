from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from reviews.forms import LeaveReviewForm, UpdateReviewForm
from reviews.models import Review
from schedule.models import Slot

User = get_user_model()


class MentorProfileView(View):
    def get(self, request, mentor_id, *args, **kwargs):
        mentor = User.objects.get(pk=mentor_id)
        reviews = Review.objects.filter(mentor=mentor)
        slot = Review.objects.filter(mentor=mentor).first()
        return render(
            request,
            'reviews/mentor-profile.html',
            {'mentor': mentor, 'reviews': reviews, 'slot': slot},
        )


class LeaveReviewView(View):
    def post(self, request, booking_id):
        booking = get_object_or_404(Slot, pk=booking_id, user=request.user)
        mentor = booking.mentor
        form = LeaveReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.mentor = mentor
            review.user = request.user
            review.slot = booking
            review.save()
            return redirect('my-bookings')
        return render(request, 'reviews/leave-review.html',
                      {'form': form, 'slot': booking})
    def get(self, request, booking_id):
        booking = get_object_or_404(Slot, pk=booking_id, user=request.user)
        form = LeaveReviewForm()
        return render(request, 'reviews/leave-review.html',
                      {'form': form, 'slot': booking}
                      )


class UpdateReviewView(View):
    def post(self, request, review_id):
        review = get_object_or_404(Review, pk=review_id)
        form = UpdateReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, 'Review edited.', extra_tags='success')
            return redirect('my-bookings')
        return render(request, 'reviews/update-review.html', {'form': form})

    def get(self, request, review_id, *args, **kwargs):
        review = get_object_or_404(Review, pk=review_id)
        form = UpdateReviewForm(instance=review)
        return render(request, 'reviews/update-review.html', {'form': form})
