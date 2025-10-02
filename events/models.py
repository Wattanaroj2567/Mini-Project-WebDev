from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class Event(models.Model):
    """
    Model สำหรับเก็บข้อมูลของกิจกรรม (Event)
    """
    title = models.CharField(max_length=200, help_text="ชื่อกิจกรรม")
    description = models.TextField(help_text="รายละเอียดกิจกรรม")
    start_datetime = models.DateTimeField(
        help_text="วันและเวลาที่เริ่มกิจกรรม")
    location = models.CharField(max_length=200, help_text="สถานที่จัดกิจกรรม")
    max_participants = models.PositiveIntegerField(
        default=100, help_text="จำนวนผู้เข้าร่วมสูงสุด")

    # ความสัมพันธ์: กิจกรรมนี้ถูกสร้างโดย User คนไหน (Organizer)
    # related_name='organized_events' ช่วยให้เราสามารถเรียกดู event ทั้งหมดที่ user คนหนึ่งสร้างได้ง่ายๆ
    organizer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='organized_events')

    def __str__(self):
        # แสดงผลในหน้า Admin ให้อ่านง่ายขึ้น
        return self.title

    def get_absolute_url(self):
        # สร้าง URL สำหรับไปยังหน้ารายละเอียดของ Event นี้
        return reverse('events:event_detail', kwargs={'pk': self.pk})


class Registration(models.Model):
    """
    Model สำหรับเก็บข้อมูลการลงทะเบียน
    ทำหน้าที่เป็นตัวกลางเชื่อมระหว่าง User และ Event
    """
    # ความสัมพันธ์: User คนไหนที่ลงทะเบียน
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='registrations')

    # ความสัมพันธ์: ลงทะเบียนใน Event ไหน
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name='registrations')

    registered_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Confirmed')

    class Meta:
        # กำหนดให้ User 1 คน สามารถลงทะเบียน Event 1 งาน ได้แค่ครั้งเดียว
        unique_together = ('user', 'event')

    def __str__(self):
        return f'{self.user.username} registered for {self.event.title}'
