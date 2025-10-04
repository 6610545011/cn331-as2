from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Room, Booking
from django.utils import timezone
from datetime import timedelta, time

class BookingAppTests(TestCase):

    def setUp(self):
        """ setup environment """
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.staff_user = User.objects.create_user(username='staffuser', password='password123', is_staff=True)
        self.room1 = Room.objects.create(room_id='R101', name='Test Room 1', capacity=10)
        self.room2 = Room.objects.create(room_id='R102', name='Test Room 2', capacity=5, is_available=False)

        self.future_time_for_existing_booking = time(14, 0)
        self.future_time_for_new_booking = time(15, 0)

        self.existing_booking = Booking.objects.create(
            user=self.staff_user,
            room=self.room1,
            booking_date=timezone.localdate(),
            start_time=self.future_time_for_existing_booking,
            end_time=time(15, 0)
        )

    def test_room_list_view(self):
        """ทดสอบว่าเห็นครบทุกห้อง"""
        response = self.client.get(reverse('room_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.room1.name)
        self.assertNotContains(response, self.room2.name)

    def test_room_detail_view_redirects_if_not_logged_in(self):
        """ทดสอบว่าจะเข้าหน้าจอง ต้องเข้า login ก่อน"""
        response = self.client.get(reverse('room_detail', args=[self.room1.id]))
        self.assertRedirects(response, f'/accounts/login/?next=/room/{self.room1.id}/')

    def test_my_bookings_view_for_logged_in_user(self):
        """ทดสอบว่า user ที่ login แล้ว สามารถเข้าหน้าจองได้"""
        self.client.login(username='staffuser', password='password123')
        response = self.client.get(reverse('my_bookings'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.room1.name)

    def test_successful_booking(self):
        """ทดสอบการจองห้องที่ยังว่าง"""
        self.client.login(username='testuser', password='password123')
        booking_date = timezone.localdate().strftime('%Y-%m-%d')
        
        booking_time = self.future_time_for_new_booking.strftime('%H:%M')

        response = self.client.post(reverse('room_detail', args=[self.room1.id]), {
            'booking_date': booking_date,
            'start_time': booking_time,
        })
        
        self.assertRedirects(response, reverse('my_bookings'))
        self.assertTrue(Booking.objects.filter(user=self.user, room=self.room1).exists())

    def test_booking_a_taken_slot(self):
        """ทดสอบการจองห้องในเวลาที่มีคนจองแล้ว"""
        self.client.login(username='testuser', password='password123')
        
        booking_time_str = self.future_time_for_existing_booking.strftime('%H:%M')
        
        response = self.client.post(reverse('room_detail', args=[self.room1.id]), {
            'booking_date': self.existing_booking.booking_date.strftime('%Y-%m-%d'),
            'start_time': booking_time_str,
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ขออภัย, ช่วงเวลานี้เพิ่งถูกจองไป')
        self.assertFalse(Booking.objects.filter(user=self.user).exists())

    def test_booking_in_the_past(self):
        """ทดสอบการจองห้องในช่วงเวลาที่ผ่านมาแล้ว"""
        self.client.login(username='testuser', password='password123')
        yesterday = (timezone.localdate() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        response = self.client.post(reverse('room_detail', args=[self.room1.id]), {
            'booking_date': yesterday,
            'start_time': '14:00',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ไม่สามารถจองในช่วงเวลาที่ผ่านมาแล้วได้')

    def test_user_can_cancel_own_booking(self):
        """ทดสอบการยกเลิกการจองห้อง"""
        self.client.login(username='staffuser', password='password123')
        booking_id = self.existing_booking.id
        self.assertTrue(Booking.objects.filter(id=booking_id).exists())
        
        response = self.client.post(reverse('cancel_booking', args=[booking_id]))

        self.assertRedirects(response, reverse('my_bookings'))
        self.assertFalse(Booking.objects.filter(id=booking_id).exists())

    def test_user_cannot_book_two_rooms_at_same_time(self):
        """ทดสอบว่า user จองได้ทีละ 1 ห้อง"""
        self.client.login(username='staffuser', password='password123')
        room3 = Room.objects.create(room_id='R103', name='Test Room 3', capacity=2)
        
        booking_time_str = self.future_time_for_existing_booking.strftime('%H:%M')

        response = self.client.post(reverse('room_detail', args=[room3.id]), {
            'booking_date': self.existing_booking.booking_date.strftime('%Y-%m-%d'),
            'start_time': booking_time_str,
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'คุณมีการจองอื่นในเวลา')

    def test_regular_user_cannot_book_in_advance(self):
        """ทดสอบว่า user ไม่สามารถจองเวลาในวันถัดไปได้ (จองล่วงหน้าไม่ได้)"""
        self.client.login(username='testuser', password='password123')
        tomorrow = (timezone.localdate() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        response = self.client.post(reverse('room_detail', args=[self.room1.id]), {
            'booking_date': tomorrow,
            'start_time': '09:00',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'คุณไม่ได้รับอนุญาตให้จองล่วงหน้า')

    def test_staff_can_book_in_advance(self):
        """ทดสอบว่า staff สามารถจองเวลาในวันถัด ๆ ไปได้ (จองล่วงหน้าได้)"""
        self.client.login(username='staffuser', password='password123')
        tomorrow = (timezone.localdate() + timedelta(days=1)).strftime('%Y-%m-%d')
        response = self.client.post(reverse('room_detail', args=[self.room1.id]), {
            'booking_date': tomorrow,
            'start_time': '14:00',
        })

        self.assertRedirects(response, reverse('my_bookings'))
        self.assertTrue(Booking.objects.filter(user=self.staff_user, booking_date__year=int(tomorrow[:4])).exists())