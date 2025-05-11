from django import forms
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError

User = get_user_model()


class RegisterForm(UserCreationForm):

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')


    def clean_username(self):
        username = self.cleaned_data['username']
        if ' ' in username:
            raise ValidationError('Username cannot contain spaces.')
        if not username.strip():
            raise ValidationError("Username cannot be empty or contain only spaces.")
        return username


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Username or Email", widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Password", widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def clean(self):
        username_or_email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username_or_email and password:
            # Пытаемся найти пользователя по email или username
            try:
                user = User.objects.get(email=username_or_email)
                username = user.username  # конвертируем email → username
            except User.DoesNotExist:
                username = username_or_email

            self.user_cache = authenticate(self.request, username=username, password=password)

            if self.user_cache is None:
                raise ValidationError("Invalid login credentials")
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class UpdateUserForm(forms.ModelForm):

    password = None

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

    def clean_username(self):
        username = self.cleaned_data['username']
        if ' ' in username:
            raise ValidationError("Username cannot contain spaces.")
        if not username.strip():
            raise ValidationError("Username cannot be empty or contain only spaces.")
        return username
