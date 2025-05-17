from django.urls import path

from . import views

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('mentor-slots/', views.MentorSlotsView.as_view(), name='mentor-slots'),
    path('create-slot/', views.CreateSlotView.as_view(), name='create-slot'),
    path('update-slot/<int:slot_id>', views.UpdateSlotView.as_view(), name='update-slot'),
    path('delete-slot/<int:slot_id>', views.DeleteSlotView.as_view(), name='delete-slot'),
]
