from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q
from django.urls import reverse
from .models import Event, Registration, RegistrationStatus

# --- Views สำหรับแสดงผลรายการและรายละเอียด (สำหรับทุกคน) ---


class EventListView(ListView):
    """แสดงรายการกิจกรรมทั้งหมด"""
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'
    ordering = ['-start_datetime']  # เรียงจากกิจกรรมล่าสุดก่อน

    def get_queryset(self):
        return (
            Event.objects.select_related('organizer')
            .annotate(
                _confirmed_participants_count=Count(
                    'registrations',
                    filter=Q(registrations__status=RegistrationStatus.CONFIRMED),
                    distinct=True,
                )
            )
            .order_by(*self.ordering)
        )


class EventDetailView(DetailView):
    """แสดงรายละเอียดของกิจกรรม"""
    model = Event
    template_name = 'events/event_detail.html'
    context_object_name = 'event'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.object
        context['confirmed_count'] = event.confirmed_participants_count
        context['remaining_slots'] = event.remaining_slots
        context['is_full'] = event.is_full

        registration = None
        if self.request.user.is_authenticated:
            registration = Registration.objects.filter(
                event=event,
                user=self.request.user,
            ).first()
            context['registration'] = registration
            context['is_registered'] = registration is not None and registration.status == RegistrationStatus.CONFIRMED
            context['registration_status'] = registration.status if registration else None
            context['registration_status_display'] = registration.get_status_display(
            ) if registration else None
        else:
            context['is_registered'] = False
            context['registration_status'] = None
            context['registration_status_display'] = None

        return context

# --- Views สำหรับจัดการกิจกรรม (CRUD - สำหรับ Organizer) ---


class OrganizerRequiredMixin(UserPassesTestMixin):
    """Mixin สำหรับตรวจสอบว่า User เป็นเจ้าของ Event หรือไม่"""
    raise_exception = True

    def test_func(self):
        event = self.get_object()
        return self.request.user == event.organizer


class EventCreateView(LoginRequiredMixin, CreateView):
    """หน้าสร้างกิจกรรมใหม่ (ต้อง Login)"""
    model = Event
    fields = ['title', 'description', 'start_datetime',
              'location', 'max_participants', 'category', 'allow_male', 'allow_female']
    template_name = 'events/event_form.html'

    def form_valid(self, form):
        # กำหนดให้ organizer คือ user ที่ login อยู่โดยอัตโนมัติ
        form.instance.organizer = self.request.user
        messages.success(self.request, 'สร้างกิจกรรมสำเร็จแล้ว!')
        return super().form_valid(form)


class EventUpdateView(LoginRequiredMixin, OrganizerRequiredMixin, UpdateView):
    """หน้าแก้ไขกิจกรรม (ต้อง Login และเป็นเจ้าของ)"""
    model = Event
    fields = ['title', 'description', 'start_datetime',
              'location', 'max_participants', 'category', 'allow_male', 'allow_female']
    template_name = 'events/event_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'แก้ไขกิจกรรมสำเร็จแล้ว!')
        return super().form_valid(form)


# --- Views สำหรับจัดการการลงทะเบียน (สำหรับ Participant) ---


@login_required
def event_delete(request, pk):
    """ลบกิจกรรมผ่าน POST บนหน้าเดียวกัน"""
    event = get_object_or_404(Event, pk=pk)
    if event.organizer != request.user:
        return HttpResponseForbidden()
    if request.method == 'POST':
        event.delete()
        messages.success(request, 'ลบกิจกรรมสำเร็จแล้ว!')
        return redirect('events:event_list')
    messages.warning(request, 'กรุณายืนยันการลบกิจกรรมผ่านปุ่มยืนยัน')
    return redirect('events:event_detail', pk=pk)


@login_required
def event_register(request, pk):
    """Logic สำหรับการลงทะเบียน"""
    event = get_object_or_404(Event, pk=pk)

    registration = Registration.objects.filter(
        user=request.user,
        event=event,
    ).first()

    if registration and registration.status == RegistrationStatus.CONFIRMED:
        messages.info(request, 'คุณได้ลงทะเบียนกิจกรรมนี้ไปแล้ว')
        return redirect('events:event_detail', pk=pk)

    if event.is_full and not (registration and registration.status == RegistrationStatus.CONFIRMED):
        messages.error(
            request, f'กิจกรรม "{event.title}" เต็มแล้ว ไม่สามารถลงทะเบียนเพิ่มเติมได้')
        return redirect('events:event_detail', pk=pk)

    if registration:
        registration.status = RegistrationStatus.CONFIRMED
        registration.registered_at = timezone.now()
        registration.save(update_fields=['status', 'registered_at'])
    else:
        Registration.objects.create(user=request.user, event=event)

    messages.success(
        request, f'คุณได้ลงทะเบียนเข้าร่วมกิจกรรม "{event.title}" สำเร็จแล้ว')
    return redirect('events:event_detail', pk=pk)


@login_required
def event_unregister(request, pk):
    """Logic สำหรับการยกเลิกการลงทะเบียน"""
    event = get_object_or_404(Event, pk=pk)

    registration = Registration.objects.filter(
        user=request.user, event=event).first()
    if not registration:
        messages.info(request, 'คุณยังไม่ได้ลงทะเบียนกิจกรรมนี้')
        return redirect('events:event_detail', pk=pk)

    if registration.status == RegistrationStatus.CANCELLED:
        messages.info(request, 'คุณได้ยกเลิกการลงทะเบียนกิจกรรมนี้แล้ว')
        return redirect('events:event_detail', pk=pk)

    registration.status = RegistrationStatus.CANCELLED
    registration.save(update_fields=['status'])
    messages.success(
        request, f'คุณได้ยกเลิกการลงทะเบียนกิจกรรม "{event.title}" แล้ว')
    return redirect('events:event_detail', pk=pk)

# --- Views สำหรับหน้าโปรไฟล์ส่วนตัว ---


class MyOrganizedEventsView(LoginRequiredMixin, ListView):
    """แสดงรายการกิจกรรมที่ฉันสร้าง"""
    model = Event
    template_name = 'events/my_organized_events.html'
    context_object_name = 'events'

    def get_queryset(self):
        # ค้นหาเฉพาะ event ที่มี organizer เป็น user ที่ login อยู่
        return (
            Event.objects.filter(organizer=self.request.user)
            .select_related('organizer')
            .annotate(
                _confirmed_participants_count=Count(
                    'registrations',
                    filter=Q(registrations__status=RegistrationStatus.CONFIRMED),
                    distinct=True,
                )
            )
            .order_by('-start_datetime')
        )


class MyRegistrationsView(LoginRequiredMixin, ListView):
    """แสดงรายการกิจกรรมที่ฉันลงทะเบียน"""
    model = Registration
    template_name = 'events/my_registrations.html'
    context_object_name = 'registrations'

    def get_queryset(self):
        # ค้นหาเฉพาะ registration ที่มี user เป็น user ที่ login อยู่
        return Registration.objects.filter(user=self.request.user).select_related('event').order_by('-event__start_datetime')
