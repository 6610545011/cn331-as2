from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Room, Booking
from django.utils import timezone
from datetime import datetime, time as dt_time

def room_list(request):
    """
    View สำหรับแสดงรายการห้องทั้งหมดที่เปิดให้จอง (is_available=True)
    """
    rooms = Room.objects.filter(is_available=True)
    context = {
        'rooms': rooms
    }
    return render(request, 'booking/room_list.html', context)

@login_required
def room_detail(request, room_id):
    """
    View สำหรับแสดงรายละเอียดห้อง, ตรวจสอบเวลาว่าง, และจัดการการจอง
    (เวอร์ชันไม่ใช้ JavaScript)
    """
    room = get_object_or_404(Room, id=room_id)
    today_date = timezone.localdate()
    
    # รับวันที่ที่ผู้ใช้เลือกจากการกดปุ่ม "ตรวจสอบเวลาว่าง" ผ่าน GET parameter
    selected_date_str = request.GET.get('date', None)
    time_slots = []

    # ถ้ามีการเลือกวันที่เข้ามา, สร้างรายการเวลาพร้อมสถานะ
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
            
            bookings_on_date = Booking.objects.filter(room=room, booking_date=selected_date)
            booked_start_times = [b.start_time.strftime('%H:%M') for b in bookings_on_date]
            now = timezone.localtime(timezone.now())

            for hour in range(8, 17):
                time_str = f"{hour:02d}:00"
                slot_time = dt_time(hour, 0)
                slot_datetime = timezone.make_aware(datetime.combine(selected_date, slot_time))
                
                status = 'available'
                if time_str in booked_start_times:
                    status = 'booked'
                elif slot_datetime < now:
                    status = 'past'
                
                time_slots.append({'time': time_str, 'status': status})

        except ValueError:
            messages.error(request, "รูปแบบวันที่ไม่ถูกต้อง")
            selected_date_str = None

    # จัดการเมื่อมีการส่งฟอร์มการจอง (POST request)
    if request.method == 'POST':
        date_str = request.POST.get('booking_date')
        start_time_str = request.POST.get('start_time')

        try:
            booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
        except (ValueError, TypeError):
            messages.error(request, 'ข้อมูลวันที่หรือเวลาไม่ถูกต้อง')
            return redirect('room_detail', room_id=room.id)

        # ===== ลำดับการตรวจสอบที่แก้ไขแล้ว =====

        # 1. ตรวจสอบว่าห้องนี้ในช่วงเวลานี้ถูกจองไปแล้วหรือยัง? (สำคัญที่สุด)
        if Booking.objects.filter(room=room, booking_date=booking_date, start_time=start_time).exists():
            messages.error(request, 'ขออภัย, ช่วงเวลานี้เพิ่งถูกจองไป')
            return redirect('room_detail', room_id=room.id)

        # 2. ตรวจสอบว่า User คนนี้จองห้องอื่นในเวลาเดียวกันไปแล้วหรือยัง?
        if Booking.objects.filter(user=request.user, booking_date=booking_date, start_time=start_time).exists():
            messages.error(request, f'คุณมีการจองอื่นในเวลา {start_time_str} ของวันที่ {date_str} อยู่แล้ว')
            return redirect('room_detail', room_id=room.id)

        # 3. ตรวจสอบว่าจองเวลาย้อนหลังหรือไม่
        proposed_booking_dt = datetime.combine(booking_date, start_time)
        aware_proposed_dt = timezone.make_aware(proposed_booking_dt)
        if aware_proposed_dt < timezone.now():
            messages.error(request, 'ไม่สามารถจองในช่วงเวลาที่ผ่านมาแล้วได้')
            return redirect('room_detail', room_id=room.id)

        # 4. ตรวจสอบ Role: User ธรรมดาจองล่วงหน้าไม่ได้
        if not request.user.is_staff and booking_date > today_date:
            messages.error(request, 'คุณไม่ได้รับอนุญาตให้จองล่วงหน้า')
            return redirect('room_detail', room_id=room.id)
        
        # --- ถ้าผ่านทุกการตรวจสอบ ---
        end_hour = start_time.hour + 1
        end_time = dt_time(end_hour, 0)
        Booking.objects.create(
            user=request.user, room=room, booking_date=booking_date,
            start_time=start_time, end_time=end_time
        )
        messages.success(request, f'คุณได้จองห้อง {room.name} สำเร็จแล้ว')
        return redirect('my_bookings')

    # ดึงข้อมูลการจองทั้งหมดสำหรับแสดงให้ Staff ดู
    bookings_for_staff = None
    if request.user.is_staff:
        bookings_for_staff = Booking.objects.filter(room=room).order_by('-booking_date', '-start_time')

    context = {
        'room': room,
        'today_date': today_date.strftime('%Y-%m-%d'),
        'selected_date': selected_date_str,
        'time_slots': time_slots,
        'bookings_for_staff': bookings_for_staff,
    }
    return render(request, 'booking/room_detail.html', context)

@login_required
def my_bookings(request):
    """
    View สำหรับแสดงรายการจองทั้งหมดของผู้ใช้ที่ login อยู่
    """
    bookings = Booking.objects.filter(user=request.user).order_by('-booking_date', '-start_time')
    context = {
        'bookings': bookings
    }
    return render(request, 'booking/my_bookings.html', context)

@login_required
def cancel_booking(request, booking_id):
    """
    View สำหรับยกเลิกการจอง
    """
    # ดึงข้อมูลการจองโดยระบุว่าเป็นของ user ที่ login อยู่เท่านั้น เพื่อความปลอดภัย
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if request.method == 'POST':
        booking.delete()
        messages.success(request, 'การจองของคุณถูกยกเลิกเรียบร้อยแล้ว')
        return redirect('my_bookings')

    # หากไม่ใช่ POST request (เช่น เข้าผ่าน URL ตรงๆ) ให้ redirect กลับไปเฉยๆ
    return redirect('my_bookings')