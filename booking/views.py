from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Room, Booking
from django.utils import timezone
from datetime import datetime, time as dt_time


def room_list(request):
    rooms = Room.objects.filter(is_available=True)
    context = {"rooms": rooms}
    return render(request, "booking/room_list.html", context)


@login_required
def room_detail(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    today_date = timezone.localdate()

    selected_date_str = request.GET.get("date", None)
    time_slots = []

    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()

            bookings_on_date = Booking.objects.filter(
                room=room, booking_date=selected_date
            )
            booked_start_times = [
                b.start_time.strftime("%H:%M") for b in bookings_on_date
            ]
            now = timezone.localtime(timezone.now())

            for hour in range(8, 17):
                time_str = f"{hour:02d}:00"
                slot_time = dt_time(hour, 0)
                slot_datetime = timezone.make_aware(
                    datetime.combine(selected_date, slot_time)
                )

                status = "available"
                if time_str in booked_start_times:
                    status = "booked"
                elif slot_datetime < now:
                    status = "past"

                time_slots.append({"time": time_str, "status": status})

        except ValueError:
            messages.error(request, "รูปแบบวันที่ไม่ถูกต้อง")
            selected_date_str = None

    if request.method == "POST":
        date_str = request.POST.get("booking_date")
        start_time_str = request.POST.get("start_time")

        if not start_time_str:
            messages.error(request, "กรุณาเลือกช่วงเวลาที่ต้องการจอง")

            return redirect(f"{request.path_info}?date={date_str}")

        try:
            booking_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            start_time = datetime.strptime(start_time_str, "%H:%M").time()
        except (ValueError, TypeError):
            messages.error(request, "ข้อมูลวันที่หรือเวลาไม่ถูกต้อง")
            return redirect("room_detail", room_id=room.id)

        proposed_booking_dt = datetime.combine(booking_date, start_time)
        aware_proposed_dt = timezone.make_aware(proposed_booking_dt)
        if aware_proposed_dt < timezone.now():
            messages.error(request, "ไม่สามารถจองในช่วงเวลาที่ผ่านมาแล้วได้")
            return redirect(f"{request.path_info}?date={date_str}")

        if not request.user.is_staff and booking_date > today_date:
            messages.error(request, "คุณไม่ได้รับอนุญาตให้จองล่วงหน้า")
            return redirect(f"{request.path_info}?date={date_str}")

        if Booking.objects.filter(
            room=room, booking_date=booking_date, start_time=start_time
        ).exists():
            messages.error(request, "ขออภัย, ช่วงเวลานี้เพิ่งถูกจองไป")
            return redirect(f"{request.path_info}?date={date_str}")

        if Booking.objects.filter(
            user=request.user, booking_date=booking_date, start_time=start_time
        ).exists():
            messages.error(
                request, f"คุณมีการจองอื่นในเวลา {start_time_str} ของวันที่ {date_str} อยู่แล้ว"
            )
            return redirect(f"{request.path_info}?date={date_str}")

        end_hour = start_time.hour + 1
        end_time = dt_time(end_hour, 0)
        Booking.objects.create(
            user=request.user,
            room=room,
            booking_date=booking_date,
            start_time=start_time,
            end_time=end_time,
        )
        messages.success(request, f"คุณได้จองห้อง {room.name} สำเร็จแล้ว")
        return redirect("my_bookings")

    bookings_for_staff = None
    if request.user.is_staff:
        bookings_for_staff = Booking.objects.filter(room=room).order_by(
            "-booking_date", "-start_time"
        )

    context = {
        "room": room,
        "today_date": today_date.strftime("%Y-%m-%d"),
        "selected_date": selected_date_str,
        "time_slots": time_slots,
        "bookings_for_staff": bookings_for_staff,
    }
    return render(request, "booking/room_detail.html", context)


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).order_by(
        "-booking_date", "-start_time"
    )
    context = {"bookings": bookings}
    return render(request, "booking/my_bookings.html", context)


@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if request.method == "POST":
        booking.delete()
        messages.success(request, "การจองของคุณถูกยกเลิกเรียบร้อยแล้ว")
        return redirect("my_bookings")
    return redirect("my_bookings")
