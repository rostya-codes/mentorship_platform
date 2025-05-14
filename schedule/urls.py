from django.urls import path

from . import views

urlpatterns = [
    path('', views.SlotListView.as_view(), name='slots_list'),
    path('book/<int:slot_id>/', views.BookSlotView.as_view(), name='book_slot'),
    path('cancel/<int:booking_id>/', views.CancelBookingView.as_view(), name='cancel_booking'),
    path('my-bookings/', views.MyBookingsView.as_view(), name='my_bookings'),
    path('mentor_slots/', views.MentorSlotsView.as_view(), name='mentor_slots'),
]
