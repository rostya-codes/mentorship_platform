from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView
from rest_framework_simplejwt.views import TokenObtainPairView

from api.serializers import MyTokenObtainPairSerializer
from .forms import RegisterForm, UpdateUserForm
from .tasks import register_email_confirm
from .utils import decode_uid, encode_uid, generate_token, verify_token

User = get_user_model()


class RegisterView(View):
    def get(self, request):
        form = RegisterForm()
        return render(request, 'accounts/register.html', {'form': form})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # деактивуємо до підтвердження
            user.save()

            self.send_verification_email(request, user)

            # Сторінка, що повідомляє про відправку листа
            return render(request, 'accounts/email-verification-sent.html')
        return render(request, 'accounts/register.html', {'form': form})

    def send_verification_email(self, request, user):
        token = generate_token(user)
        uid = encode_uid(user)
        verification_link = request.build_absolute_uri(
            reverse('email-verification', kwargs={'uidb64': uid, 'token': token})
        )

        register_email_confirm.delay(user_id=user.id, verification_link=verification_link)
        messages.success(request, 'Check your email inbox and approve your email.')


class EmailVerificationView(View):
    def get(self, request, uidb64, token):
        uid = decode_uid(uidb64)
        if uid is None:
            return render(request, 'accounts/email-verification-failed.html')

        try:
            user = User.objects.get(pk=uid)
        except User.DoesNotExist:
            return render(request, 'accounts/email-verification-failed.html')

        if verify_token(user, token):
            user.is_active = True
            user.save()
            login(request, user)
            return render(request, 'accounts/email-verification-success.html')
        else:
            return render(request, 'accounts/email-verification-failed.html')


@method_decorator(login_required, name='dispatch')
class ProfileView(View):
    def get(self, request, *args, **kwargs):
        form = UpdateUserForm(instance=request.user)
        return render(request, 'accounts/profile.html', {'form': form})

    def post(self, request):
        form = UpdateUserForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
        return render(request, 'accounts/profile.html', {'form': form})


@login_required(login_url='login')
def logout_user(request):
    logout(request)
    return redirect('login')


class BlockedPage(TemplateView):
    template_name = 'accounts/blocked_page.html'


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
