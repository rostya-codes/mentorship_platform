from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import LoginForm

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='accounts/login.html',
            authentication_form=LoginForm
        ),
        name='login'
    ),
    path('logout/', views.logout_user, name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('user-profile/<str:username>', views.UserProfileView.as_view(), name='user-profile'),
    path('blocked_page/', views.BlockedPage.as_view(), name='blocked_page'),

    # Email verification
    path('email-verification/<uidb64>/<token>/', views.EmailVerificationView.as_view(), name='email-verification'),
]
