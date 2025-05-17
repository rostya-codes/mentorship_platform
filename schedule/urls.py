from django.urls import path

from . import views

urlpatterns = [
    path('', views.SlotListView.as_view(), name='slots-list'),
    path('book/<int:slot_id>/', views.BookSlotView.as_view(), name='book-slot'),
    path('cancel/<int:booking_id>/', views.CancelBookingView.as_view(), name='cancel-booking'),
    path('my-bookings/', views.MyBookingsView.as_view(), name='my-bookings'),
    path('mentor-slots/', views.MentorSlotsView.as_view(), name='mentor-slots'),
    path('create-slot/', views.CreateSlotView.as_view(), name='create-slot'),
    path('update-slot/<int:slot_id>', views.UpdateSlotView.as_view(), name='update-slot'),
    path('delete-slot/<int:slot_id>', views.DeleteSlotView.as_view(), name='delete-slot'),
]
