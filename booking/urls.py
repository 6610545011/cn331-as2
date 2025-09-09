from django.urls import path
from . import views

urlpatterns = [
    path("", views.room_list, name="room_list"),
    path("room/<int:room_id>/", views.room_detail, name="room_detail"),
    path("my_bookings/", views.my_bookings, name="my_bookings"),
    path(
        "booking/cancel/<int:booking_id>/", views.cancel_booking, name="cancel_booking"
    ),
]
