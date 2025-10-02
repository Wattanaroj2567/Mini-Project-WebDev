# EventRegis+ Backend Handoff

ระบบ EventRegis+ คือเว็บแอปสำหรับจัดการกิจกรรม ประกอบด้วยโมดูลสร้าง/แก้ไข/ลบกิจกรรม ระบบลงทะเบียนของผู้ร่วมงาน และการจัดการบัญชีผู้ใช้ผ่าน Django Allauth โค้ดฝั่งแบ็กเอนด์อยู่ในระดับพร้อมใช้งาน เหลือการตกแต่งหน้าตาและประสบการณ์ผู้ใช้ให้ทีม Front-End เข้ามาดำเนินการต่อ

## ภาพรวมเทคโนโลยี
- **Framework หลัก**: Django 5.2 + Django Allauth
- **ฐานข้อมูล**: SQLite (ไฟล์ `db.sqlite3`)
- **UI Toolkit**: TailwindCSS + daisyUI (ผ่านแอป `theme`)
- **ระบบข้อความ**: Django messages (toast บน `base.html`)

> รายละเอียดฟังก์ชันเชิงลึกถูกสรุปไว้ใน `docs/backend_canvas.md`

## เตรียมสภาพแวดล้อม
> โปรเจ็กต์ตั้งต้นจาก branch `dev` (ตั้งเป็น default แล้ว) ให้เพื่อนดึง branch นี้เสมอเมื่อเริ่มทำงาน

### บน Windows (PowerShell)
```powershell
git clone https://github.com/Wattanaroj2567/Mini-Project-WebDev.git --branch dev --single-branch
cd Mini-Project-WebDev
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env    # หากมีไฟล์ตัวอย่าง
py manage.py migrate
py manage.py createsuperuser
py manage.py runserver
```

### บน macOS / Linux (Shell)
```bash
git clone https://github.com/Wattanaroj2567/Mini-Project-WebDev.git --branch dev --single-branch
cd Mini-Project-WebDev
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # ถ้ามีไฟล์ตัวอย่าง
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

- ตั้งค่า `SECRET_KEY` และ `DEBUG` ใน `.env`
- เส้นทางหลักของระบบอยู่ที่ `http://127.0.0.1:8000/`
- ส่วนจัดการผู้ใช้ (signup/login/logout/password flows) ใช้เส้นทางจาก Allauth ภายใต้ prefix `/accounts/`

## โครงสร้างโปรเจกต์ที่เกี่ยวข้อง
```
event-regis-project/
├── events/                 # Django app หลัก (models, views, urls)
│   └── templates/
│       ├── account/        # override template ของ allauth
│       └── events/         # เทมเพลตฟังก์ชันกิจกรรม
├── theme/templates/base.html
├── docs/backend_canvas.md  # เอกสารสรุปเส้นทางและ logic backend
├── db.sqlite3
├── manage.py
└── README.md
```

## สรุปฟังก์ชันหลัก
| Path | Method | View | หน้าที่ | Template |
|------|--------|------|---------|----------|
| `/` | GET | `EventListView` | แสดงกิจกรรมทั้งหมด | `events/event_list.html` |
| `/<int:pk>/` | GET | `EventDetailView` | รายละเอียดกิจกรรม + ปุ่มลงทะเบียน/จัดการ | `events/event_detail.html` |
| `/create/` | GET/POST | `EventCreateView` | สร้างกิจกรรมใหม่ (เฉพาะผู้ล็อกอิน) | `events/event_form.html` |
| `/<int:pk>/update/` | GET/POST | `EventUpdateView` | แก้ไขกิจกรรมของตนเอง | `events/event_form.html` |
| `/<int:pk>/delete/` | POST | `EventDeleteView` | ลบกิจกรรม (พร้อม toast ข้อความ) | `events/event_confirm_delete.html` |
| `/<int:pk>/register/` | POST | `event_register` | ลงทะเบียนเข้าร่วมกิจกรรม | redirect → รายละเอียด |
| `/<int:pk>/unregister/` | POST | `event_unregister` | ยกเลิกรายการลงทะเบียน | redirect → รายละเอียด |
| `/my-events/` | GET | `MyOrganizedEventsView` | กิจกรรมที่ผู้ใช้สร้าง | `events/my_organized_events.html` |
| `/my-registrations/` | GET | `MyRegistrationsView` | กิจกรรมที่ผู้ใช้ลงทะเบียนไว้ | `events/my_registrations.html` |

### ตรรกะสำคัญฝั่งลงทะเบียน
- กันการลงทะเบียนซ้ำด้วยการตรวจ `Registration` ที่มีอยู่ก่อน
- เช็กจำนวนผู้ลงทะเบียน `event.registrations.count()` ไม่ให้เกิน `max_participants`
- ใช้ `messages.info/success/error` เพื่อสื่อสารผลลัพธ์กลับไปยังผู้ใช้

## Checklist สำหรับทีม Front-End
1. **ออกแบบ UX/UI** บนเทมเพลตใน `events/templates/events/` และ `events/templates/account/` ให้สอดคล้องกับ guideline วิชา (Tailwind + daisyUI)
2. **ปรับปรุงฟอร์ม** (เช่น input `datetime-local`, `number`) ให้อยู่ในรูปแบบที่ใช้งานง่าย พร้อม validation ฝั่งเบราว์เซอร์ถ้าจำเป็น
3. **ตกแต่ง Toast/Modal** ใน `theme/templates/base.html` เพื่อให้ messages อ่านง่ายและเหมาะกับดีไซน์รวม
4. **ออกแบบหน้า account** (login/signup/password change/reset) ให้มี branding ชัดเจน จัด layout ฟอร์มเองแทน `{{ form.as_p }}` และเน้น error message/ลิงก์สลับหน้า
5. **เพิ่ม UX รายละเอียดกิจกรรม** เช่น แสดงจำนวนผู้ลงทะเบียนปัจจุบัน, แสดงปุ่ม disable เมื่อเต็ม, แสดงข้อมูล organizer อย่างชัดเจน
6. **ตรวจครอบคลุม flow** (signup/login/logout/password reset, create/update/delete event, register/unregister) ทั้ง Desktop และ Mobile
7. **จัดทำ assets เพิ่มเติม** (โลโก้, รูปประกอบ) ถ้าต้องการ และใส่ไว้ใน static directory

## การทดสอบ
- ใช้ `python manage.py check` เพื่อตรวจสุขภาพโปรเจกต์ (ปัจจุบันผ่านแล้ว)
- เสนอให้เพิ่ม unit test สำหรับฟังก์ชันลงทะเบียนเมื่อมีเวลาพัฒนาเพิ่มเติม (`events/tests.py`)

## ขั้นตอนส่งงานขึ้น Git (dev branch)
```bash
# กำหนด safe directory (ทำครั้งเดียว ต่อให้ใช้ Ubuntu หรือ Windows)
git config --global --add safe.directory '*'

# ตั้ง remote (ทำครั้งแรก)
git remote add origin https://github.com/Wattanaroj2567/Mini-Project-WebDev.git

# ตรวจสอบ branch ปัจจุบันว่าเป็น dev
git branch --show-current

# ถ้าแสดงเป็น main หรือ branch อื่น ให้สลับไป dev
git checkout dev            # dev มีอยู่แล้วใน remote
# หรือถ้าจำเป็นต้องสร้าง local branch ครั้งแรก
# git checkout -b dev origin/dev

# เพิ่มไฟล์ทั้งหมดที่แก้ไข
git add .

# สร้าง commit พร้อมข้อความ
git commit -m "คำอธิบายการเปลี่ยนแปลง"

# ดันขึ้น remote dev (ครั้งแรกใช้ -u ตั้ง upstream)
git push -u origin dev

# ครั้งต่อไปสามารถใช้
git push
```

## ทีมผู้พัฒนา
- **Back-End**: นายวรรธนโรจน์ บุตรดี (66114540621)
- **Front-End**: นายณัฐพงษ์ ดีบุตร (66114540229)

หากมีคำถามเพิ่มเติมเกี่ยวกับตรรกะแบ็กเอนด์ สามารถอ้างอิงเอกสาร `docs/backend_canvas.md` หรือสอบถามผู้พัฒนาแบ็กเอนด์โดยตรงครับ
