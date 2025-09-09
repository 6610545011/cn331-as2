from django.db import models
from django.contrib.auth.models import User


class Room(models.Model):
    room_id = models.CharField(max_length=10, unique=True, verbose_name="รหัสห้อง")
    name = models.CharField(max_length=100, verbose_name="ชื่อห้อง")
    capacity = models.IntegerField(verbose_name="ความจุ")
    max_booking_hours = models.PositiveIntegerField(
        default=1, verbose_name="จำนวนชั่วโมงที่จองได้สูงสุด"
    )
    is_available = models.BooleanField(default=True, verbose_name="สถานะเปิด/ปิด")

    def __str__(self):
        return f"{self.room_id} - {self.name}"


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ผู้จอง")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, verbose_name="ห้องที่จอง")
    booking_date = models.DateField(verbose_name="วันที่จอง")
    start_time = models.TimeField(verbose_name="เวลาเริ่มต้น")
    end_time = models.TimeField(verbose_name="เวลาสิ้นสุด")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} จองห้อง {self.room.name} วันที่ {self.booking_date} เวลา {self.start_time} - {self.end_time}"

    class Meta:
        unique_together = ("room", "booking_date", "start_time")
