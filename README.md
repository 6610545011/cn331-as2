# cn331-as2

```
      /\_/\              /\_/\         
     ( -.- )            ( o.o )        
      > ^ <              > ^ <
     /  |  \            /  |  \
    /   |   \          /   |   \
   (____|____)        (____|____)
```

## Classroom Booking Web Application

โปรเจคนี้เป็นเว็บแอปพลิเคชันสำหรับการจองห้องเรียน โดยมีการแบ่งการใช้งานออกเป็น **Admin** และ **User**

### Members
1. **Natrawee Chuewang** : 6610525013  
2. **Sarankorn Pongatsawachai** : 6610545011  


### Functionality

#### Admin
- เพิ่ม/ลบ/แก้ไข รหััส User , Room (รหัสห้อง, ชื่อห้อง, ความจุ, จำนวนชั่วโมงจอง, สถานะการจอง, เพิ่มรูป) ,Group เรียน, booking ผ่าน admin interface ของ Django
- admin สามารถจองห้องเรียนผ่านหน้า web จองได้หลายวันและหลายเวลา
- admin สามารถดูเวลาผู้ใช้คนไหนจอง ห้อง/เวลา ใดบ้างได้

#### User
- สามารถดู/จองห้องเรียนได้ ซึ่งจองได้คนละ 1 ชม.ต่อห้อง 
- สามารถยยกเลิกห้องที่จองได้

## Web app link
[https://tse-bookingroom-app.onrender.com](https://tse-bookingroom-app.onrender.com)

## Demo Video
[https://youtu.be/73HiDdPk2B0](https://youtu.be/73HiDdPk2B0)

## Update Unit Test
- test_room_list_view
- test_room_detail_view_redirects_if_not_logged_in
- test_my_bookings_view_for_logged_in_user
- test_successful_booking
- test_booking_a_taken_slot
- test_booking_in_the_past
- test_user_can_cancel_own_booking
- test_user_cannot_book_two_rooms_at_same_time
- test_regular_user_cannot_book_in_advance
- test_staff_can_book_in_advance
