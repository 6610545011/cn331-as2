from django.contrib import admin
from .models import Room, Booking

admin.site.site_title = "TSE-booking"
admin.site.site_header = "TSE-booking Administration"


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("room_id", "name", "capacity", "max_booking_hours", "is_available")
    list_filter = ("is_available",)
    search_fields = ("room_id", "name")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("user", "room", "booking_date", "start_time", "end_time")
    list_filter = ("room", "booking_date")
    search_fields = ("user__username", "room__name")
