from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Event, Registration

# --- Views สำหรับแสดงผลรายการและรายละเอียด (สำหรับทุกคน) ---


class EventListView(ListView):
    """แสดงรายการกิจกรรมทั้งหมด"""
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'
    ordering = ['-start_datetime']  # เรียงจากกิจกรรมล่าสุดก่อน


class EventDetailView(DetailView):
    """แสดงรายละเอียดของกิจกรรม"""
    model = Event
    template_name = 'events/event_detail.html'
    context_object_name = 'event'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            # เช็คว่า user ที่ login อยู่ ได้ลงทะเบียน event นี้แล้วหรือยัง
            context['is_registered'] = Registration.objects.filter(
                event=self.object,
                user=self.request.user
            ).exists()
        return context

# --- Views สำหรับจัดการกิจกรรม (CRUD - สำหรับ Organizer) ---


class OrganizerRequiredMixin(UserPassesTestMixin):
    """Mixin สำหรับตรวจสอบว่า User เป็นเจ้าของ Event หรือไม่"""

    def test_func(self):
        event = self.get_object()
        return self.request.user == event.organizer


class EventCreateView(LoginRequiredMixin, CreateView):
    """หน้าสร้างกิจกรรมใหม่ (ต้อง Login)"""
    model = Event
    fields = ['title', 'description', 'start_datetime',
              'location', 'max_participants']
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
              'location', 'max_participants']
    template_name = 'events/event_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'แก้ไขกิจกรรมสำเร็จแล้ว!')
        return super().form_valid(form)


class EventDeleteView(LoginRequiredMixin, OrganizerRequiredMixin, DeleteView):
    """หน้าลบกิจกรรม (ต้อง Login และเป็นเจ้าของ)"""
    model = Event
    template_name = 'events/event_confirm_delete.html'
    success_url = reverse_lazy('events:event_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'ลบกิจกรรมสำเร็จแล้ว!')
        return super().delete(request, *args, **kwargs)


# --- Views สำหรับจัดการการลงทะเบียน (สำหรับ Participant) ---

@login_required
def event_register(request, pk):
    """Logic สำหรับการลงทะเบียน"""
    event = get_object_or_404(Event, pk=pk)
    existing_registration = Registration.objects.filter(
        user=request.user,
        event=event
    )

    if existing_registration.exists():
        messages.info(request, 'คุณได้ลงทะเบียนกิจกรรมนี้ไปแล้ว')
        return redirect('events:event_detail', pk=pk)

    if event.registrations.count() >= event.max_participants:
        messages.error(
            request, f'กิจกรรม "{event.title}" เต็มแล้ว ไม่สามารถลงทะเบียนเพิ่มเติมได้')
        return redirect('events:event_detail', pk=pk)

    Registration.objects.create(user=request.user, event=event)
    messages.success(
        request, f'คุณได้ลงทะเบียนเข้าร่วมกิจกรรม "{event.title}" สำเร็จแล้ว')
    return redirect('events:event_detail', pk=pk)


@login_required
def event_unregister(request, pk):
    """Logic สำหรับการยกเลิกการลงทะเบียน"""
    event = get_object_or_404(Event, pk=pk)
    # ลบการลงทะเบียน
    Registration.objects.filter(user=request.user, event=event).delete()
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
        return Event.objects.filter(organizer=self.request.user).order_by('-start_datetime')


class MyRegistrationsView(LoginRequiredMixin, ListView):
    """แสดงรายการกิจกรรมที่ฉันลงทะเบียน"""
    model = Registration
    template_name = 'events/my_registrations.html'
    context_object_name = 'registrations'

    def get_queryset(self):
        # ค้นหาเฉพาะ registration ที่มี user เป็น user ที่ login อยู่
        return Registration.objects.filter(user=self.request.user).order_by('-event__start_datetime')
