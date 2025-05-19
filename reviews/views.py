from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.views import View

User = get_user_model()


class MentorProfileView(View):
    def get(self, request, mentor_id, *args, **kwargs):
        mentor = User.objects.get(pk=mentor_id)
        return render(request, 'reviews/mentor-profile.html', {'mentor': mentor})


class LeaveReviewView(View):
    pass
