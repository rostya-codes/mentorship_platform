from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from .forms import RegisterForm, UpdateUserForm
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

        subject = 'Confirm your email'
        message = (f'Hi {user.username},\n\nPlease verify your account by clicking the link below:\n{verification_link}'
                   f'\n\nThank you!')
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])


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


class ProfileView(View):
    def get(self, request, *args, **kwargs):
        form = UpdateUserForm(instance=request.user)
        return render(request, 'accounts/profile.html', {'form': form})

    def post(self, request):
        form = UpdateUserForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
        return render(request, 'accounts/profile.html', {'form': form})


@login_required(login_url='login')
def logout_user(request):
    logout(request)
    return redirect('login')
