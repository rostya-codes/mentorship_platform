from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from accounts.forms import RegisterForm, UpdateUserForm

User = get_user_model()


class MyUserAdmin(UserAdmin):
    add_form = RegisterForm
    form = UpdateUserForm
    model = User

    list_display = ('username', 'email', 'is_staff', 'is_active', 'is_mentor')
    list_filter = ('is_staff', 'is_active', 'is_mentor')

    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        (_("Personal Info"), {"fields": ("first_name", "last_name", "phone_number", "image")}),
        (_("Permissions"),
         {"fields": ("is_staff", "is_active", "is_mentor", "is_email_verified", "groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("last_login",)}),
        (_("Block details"), {"fields": ("blocked_until", "last_unblocked", "last_active_time")})
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
            "username", "email", "first_name", "last_name", "password1", "password2", "is_staff", "is_active")}
         ),
    )

    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)


admin.site.register(User, MyUserAdmin)
