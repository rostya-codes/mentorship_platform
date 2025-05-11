from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('add-slot/', views.add_slot, name='add_slot'),
    path('users/', views.users_list, name='user_list'),
]
