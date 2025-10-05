from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Event, EventCategory, Registration, RegistrationStatus


class EventFlowTests(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(username='organizer', password='pass1234')
        self.participant = User.objects.create_user(username='participant', password='pass1234')
        self.other_user = User.objects.create_user(username='other', password='pass1234')
        self.event = Event.objects.create(
            title='Test Event',
            description='Demo description',
            start_datetime=timezone.now() + timedelta(days=1),
            location='Bangkok',
            max_participants=1,
            category=EventCategory.GENERAL,
            organizer=self.organizer,
        )

    def test_create_event_assigns_logged_in_user_as_organizer(self):
        self.client.force_login(self.participant)
        response = self.client.post(
            reverse('events:event_create'),
            data={
                'title': 'New Event',
                'description': 'New description',
                'start_datetime': (timezone.now() + timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'),
                'location': 'Chiang Mai',
                'max_participants': 50,
                'category': EventCategory.WORKSHOP,
            },
        )
        self.assertEqual(response.status_code, 302)
        new_event = Event.objects.order_by('-id').first()
        self.assertEqual(new_event.organizer, self.participant)
        self.assertEqual(new_event.category, EventCategory.WORKSHOP)

    def test_update_event_requires_organizer(self):
        update_url = reverse('events:event_update', args=[self.event.pk])

        self.client.force_login(self.participant)
        response = self.client.get(update_url)
        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.organizer)
        response = self.client.post(
            update_url,
            data={
                'title': 'Updated Title',
                'description': 'Updated description',
                'start_datetime': (timezone.now() + timedelta(days=3)).strftime('%Y-%m-%dT%H:%M'),
                'location': 'Phuket',
                'max_participants': 25,
                'category': EventCategory.MEETUP,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.event.refresh_from_db()
        self.assertEqual(self.event.title, 'Updated Title')
        self.assertEqual(self.event.category, EventCategory.MEETUP)

    def test_registration_flow_with_cancellation_and_capacity(self):
        register_url = reverse('events:event_register', args=[self.event.pk])
        unregister_url = reverse('events:event_unregister', args=[self.event.pk])

        # Participant registers successfully
        self.client.force_login(self.participant)
        response = self.client.post(register_url, follow=True)
        self.assertEqual(response.status_code, 200)
        registration = Registration.objects.get(event=self.event, user=self.participant)
        self.assertEqual(registration.status, RegistrationStatus.CONFIRMED)

        # Attempt duplicate registration -> status unchanged
        self.client.post(register_url, follow=True)
        registration.refresh_from_db()
        self.assertEqual(registration.status, RegistrationStatus.CONFIRMED)
        self.assertEqual(Registration.objects.filter(event=self.event).count(), 1)

        # Another user cannot join because event is full
        self.client.force_login(self.other_user)
        response = self.client.post(register_url, follow=True)
        self.assertContains(response, 'เต็มแล้ว', status_code=200)
        self.assertFalse(
            Registration.objects.filter(event=self.event, user=self.other_user).exists()
        )

        # Original participant cancels
        self.client.force_login(self.participant)
        response = self.client.post(unregister_url, follow=True)
        self.assertEqual(response.status_code, 200)
        registration.refresh_from_db()
        self.assertEqual(registration.status, RegistrationStatus.CANCELLED)

        # Different user can now take the slot
        self.client.force_login(self.other_user)
        self.client.post(register_url, follow=True)
        other_registration = Registration.objects.get(event=self.event, user=self.other_user)
        self.assertEqual(other_registration.status, RegistrationStatus.CONFIRMED)

        # Original participant can join again if seat available
        self.event.max_participants = 2
        self.event.save(update_fields=['max_participants'])
        self.client.force_login(self.participant)
        self.client.post(register_url, follow=True)
        registration.refresh_from_db()
        self.assertEqual(registration.status, RegistrationStatus.CONFIRMED)
    def test_delete_event_requires_post_and_owner(self):
        delete_url = reverse('events:event_delete', args=[self.event.pk])

        # ผู้ใช้ทั่วไปห้ามลบ
        self.client.force_login(self.participant)
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Event.objects.filter(pk=self.event.pk).exists())

        # Organizer เรียก GET -> ไม่ลบและ redirect กลับหน้ารายละเอียด
        self.client.force_login(self.organizer)
        response = self.client.get(delete_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Event.objects.filter(pk=self.event.pk).exists())

        # Organizer ส่ง POST -> ลบสำเร็จและ redirect ไปหน้ารายการ
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Event.objects.filter(pk=self.event.pk).exists())


    def test_remaining_slots_reflects_confirmed_participants(self):
        self.client.force_login(self.participant)
        self.client.post(reverse('events:event_register', args=[self.event.pk]))
        self.event.refresh_from_db()
        self.assertEqual(self.event.confirmed_participants_count, 1)
        self.assertEqual(self.event.remaining_slots, 0)
        self.assertTrue(self.event.is_full)

