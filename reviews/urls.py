from django.urls import path

from . import views

urlpatterns = [
    path('mentor-profile/<int:mentor_id>/', views.MentorProfileView.as_view(), name='mentor-profile'),
    path('leave-review/<int:booking_id>/', views.LeaveReviewView.as_view(), name='leave-review'),
    path('edit-review/<int:review_id>/', views.UpdateReviewView.as_view(), name='update-review'),
]
