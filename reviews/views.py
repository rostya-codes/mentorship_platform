from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.views import View

from reviews.models import Review

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
    pass
