from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator


class EventCategory(models.TextChoices):
    GENERAL = "general", "ทั่วไป"
    WORKSHOP = "workshop", "เวิร์กช็อป"
    CONFERENCE = "conference", "สัมมนา"
    MEETUP = "meetup", "มีตติ้ง / Networking"
    ONLINE = "online", "ออนไลน์"


class RegistrationStatus(models.TextChoices):
    CONFIRMED = "Confirmed", "ยืนยันแล้ว"
    PENDING = "Pending", "รอดำเนินการ"
    CANCELLED = "Cancelled", "ยกเลิก"


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
    category = models.CharField(
        max_length=50,
        choices=EventCategory.choices,
        default=EventCategory.GENERAL,
        help_text="ประเภทของกิจกรรม",
    )
    allow_male = models.BooleanField(
        default=True, help_text="อนุญาตให้ผู้ชายเข้าร่วม")
    allow_female = models.BooleanField(
        default=True, help_text="อนุญาตให้ผู้หญิงเข้าร่วม")

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

    @property
    def confirmed_participants_count(self):
        cached_value = getattr(self, '_confirmed_participants_count', None)
        if cached_value is not None:
            return cached_value
        return self.registrations.filter(status=RegistrationStatus.CONFIRMED).count()

    @property
    def remaining_slots(self):
        return max(self.max_participants - self.confirmed_participants_count, 0)

    @property
    def allowed_gender_display(self):
        if self.allow_male and self.allow_female:
            return "ชายและหญิง"
        if self.allow_male:
            return "เฉพาะชาย"
        if self.allow_female:
            return "เฉพาะหญิง"
        return "ยังไม่เปิดรับผู้เข้าร่วม"

    @property
    def is_full(self):
        return self.confirmed_participants_count >= self.max_participants


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
    status = models.CharField(
        max_length=20,
        choices=RegistrationStatus.choices,
        default=RegistrationStatus.CONFIRMED,
    )

    class Meta:
        # กำหนดให้ User 1 คน สามารถลงทะเบียน Event 1 งาน ได้แค่ครั้งเดียว
        unique_together = ('user', 'event')

    def __str__(self):
        return f'{self.user.username} registered for {self.event.title}'
