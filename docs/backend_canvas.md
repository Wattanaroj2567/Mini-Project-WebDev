# EventRegis+ Backend Canvas

## พื้นฐานระบบ
- **App หลัก**: `events`
- **โมเดลสำคัญ**: `Event`, `Registration`
  - `Event` เก็บรายละเอียดกิจกรรมพร้อมฟิลด์ `category` (เลือกจากตัวเลือกที่ระบบเตรียมไว้)
  - `Registration` บันทึกสถานะการลงทะเบียน (Confirmed/Pending/Cancelled)
- **การยืนยันตัวตน**: Django Allauth (OAuth Google + Username/Password)
- **สิทธิ์ (Mixins/Decorators)**: `LoginRequiredMixin`, `UserPassesTestMixin`, `login_required`
- **ข้อความตอบกลับ**: Django messages framework (success/info/error)

---

## Path: `/` → `events:event_list`
- **View**: `EventListView` (`ListView`)
- **สิทธิ์**: ทุกคนเข้าถึงได้
- **หน้าที่**: แสดงรายการกิจกรรมทั้งหมด เรียงตาม `start_datetime` ล่าสุดก่อน
- **Template**: `events/event_list.html`
- **จุดเด่น**: หากผู้ใช้ล็อกอินจะเห็นปุ่ม `สร้างกิจกรรมใหม่`

## Path: `/<int:pk>/` → `events:event_detail`
- **View**: `EventDetailView` (`DetailView`)
- **สิทธิ์**: ทุกคนเข้าถึงได้
- **หน้าที่**: แสดงรายละเอียดกิจกรรมและสถานะการลงทะเบียนของผู้ใช้ที่ล็อกอิน
- **Template**: `events/event_detail.html`
- **ตรรกะเพิ่มเติม**: เพิ่มคีย์ `is_registered` ใน context เพื่อตัดสินใจแสดงปุ่มสมัคร/ยกเลิก/แก้ไข/ลบ

## Path: `/create/` → `events:event_create`
- **View**: `EventCreateView` (`CreateView` + `LoginRequiredMixin`)
- **สิทธิ์**: ต้องล็อกอิน
- **หน้าที่**: สร้างกิจกรรมใหม่จากฟอร์มมาตรฐาน
- **Template**: `events/event_form.html`
- **ฟิลด์ในฟอร์ม**: title, description, start_datetime, location, max_participants, category
- **ตรรกะเพิ่มเติม**: กำหนด `form.instance.organizer` เป็นผู้ใช้ปัจจุบัน และแสดง `messages.success`

## Path: `/<int:pk>/update/` → `events:event_update`
- **View**: `EventUpdateView` (`UpdateView` + Organizer check)
- **สิทธิ์**: ต้องล็อกอินและเป็นเจ้าของกิจกรรม (`OrganizerRequiredMixin`)
- **หน้าที่**: แก้ไขรายละเอียดกิจกรรม
- **Template**: `events/event_form.html`
- **ข้อความตอบกลับ**: `messages.success` ("แก้ไขกิจกรรมสำเร็จแล้ว!")

## Path: `/<int:pk>/delete/` → `events:event_delete`
- **View**: `EventDeleteView` (`DeleteView` + Organizer check)
- **สิทธิ์**: ต้องล็อกอินและเป็นเจ้าของกิจกรรม
- **หน้าที่**: ยืนยันและลบกิจกรรมถาวร
- **Template**: `events/event_confirm_delete.html`
- **ตรรกะเพิ่มเติม**: Override `delete()` เพื่อยิง `messages.success` ก่อน redirect ไปหน้ารายการ

## Path: `/<int:pk>/register/` → `events:event_register`
- **View**: ฟังก์ชัน `event_register` + `login_required`
- **สิทธิ์**: ผู้ใช้ที่ล็อกอินเท่านั้น
- **หน้าที่**: ลงทะเบียนผู้ใช้เข้าร่วมกิจกรรม
- **ตรรกะสำคัญ**:
  - หากพบ `Registration` ที่สถานะยังเป็น Confirmed จะแจ้งเตือนว่าลงทะเบียนแล้ว
  - หากพบรายการเดิมที่ถูกยกเลิก จะลองเปิดสถานะกลับเป็น Confirmed เมื่อยังมีที่นั่งว่าง
  - ตรวจสอบโควตาด้วยจำนวนผู้ยืนยัน (Confirmed) เท่านั้น หากเต็มจะปฏิเสธด้วย `messages.error`
  - เมื่อสำเร็จจะตั้งสถานะเป็น Confirmed และยิง `messages.success`
- **Redirect**: กลับไปหน้ารายละเอียดกิจกรรม

## Path: `/<int:pk>/unregister/` → `events:event_unregister`
- **View**: ฟังก์ชัน `event_unregister` + `login_required`
- **สิทธิ์**: ผู้ใช้ที่ล็อกอินเท่านั้น
- **หน้าที่**: ยกเลิกการลงทะเบียนของผู้ใช้ปัจจุบัน
- **ตรรกะ**: เปลี่ยนสถานะเป็น Cancelled (ไม่ลบข้อมูล) และส่ง `messages.success`
- **Redirect**: กลับไปหน้ารายละเอียดกิจกรรม

## Path: `/my-events/` → `events:my_organized_events`
- **View**: `MyOrganizedEventsView` (`ListView` + `LoginRequiredMixin`)
- **สิทธิ์**: ต้องล็อกอิน
- **หน้าที่**: แสดงรายการกิจกรรมที่ผู้ใช้ปัจจุบันเป็น organizer
- **Template**: `events/my_organized_events.html`
- **Queryset**: กรองด้วย `Event.objects.filter(organizer=request.user)`

## Path: `/my-registrations/` → `events:my_registrations`
- **View**: `MyRegistrationsView` (`ListView` + `LoginRequiredMixin`)
- **สิทธิ์**: ต้องล็อกอิน
- **หน้าที่**: แสดงกิจกรรมที่ผู้ใช้ลงทะเบียนไว้
- **Template**: `events/my_registrations.html`
- **Queryset**: `Registration.objects.filter(user=request.user)` เรียงตามวันเริ่มกิจกรรมล่าสุด

---

## Backend Validation & Messaging Checklist
- ป้องกัน duplicate registration ด้วยการตรวจ `Registration` ก่อนสร้าง
- ป้องกันการสมัครเกินจำนวนด้วยการเช็กจำนวนผู้ที่มีสถานะ Confirmed เทียบ `max_participants`
- ทุก action ที่เปลี่ยนข้อมูล (Create/Update/Delete/Register/Unregister) ส่งข้อความผ่าน Django messages ให้ UI แสดงผล
- การยกเลิกจะเปลี่ยนสถานะเป็น Cancelled เพื่อเก็บประวัติและเปิดโอกาสให้กลับมาลงทะเบียนอีกครั้ง
- สิทธิ์ organizer ถูกบังคับผ่าน `OrganizerRequiredMixin`
- เทมเพลต override ของ allauth อยู่ใน `events/templates/account` (แก้ชื่อโฟลเดอร์แล้ว)

## การทดสอบ
- `python manage.py check`
  - ผลลัพธ์: ผ่าน (ไม่มี issue)
