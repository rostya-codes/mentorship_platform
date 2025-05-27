from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.views import View

User = get_user_model()


class IndexView(View):
    def get(self, request, *args, **kwargs):
        mentors = User.objects.filter(is_mentor=True)
        return render(request, 'main/index.html', {'mentors': mentors})
