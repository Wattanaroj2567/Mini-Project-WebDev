
from django.urls import path
from . import views

# app_name ช่วยให้เราอ้างอิง URL ในแอปนี้ได้ง่ายขึ้น
# เช่น 'events:event_list'
app_name = 'events'

urlpatterns = [
    # หน้าแสดงรายการกิจกรรมทั้งหมด
    path('', views.EventListView.as_view(), name='event_list'),

    # หน้าแสดงรายละเอียดของกิจกรรม
    path('<int:pk>/', views.EventDetailView.as_view(), name='event_detail'),

    # หน้าสร้างกิจกรรมใหม่
    path('create/', views.EventCreateView.as_view(), name='event_create'),

    # หน้าแก้ไขกิจกรรม
    path('<int:pk>/update/', views.EventUpdateView.as_view(), name='event_update'),

    # ลบกิจกรรม (POST เท่านั้น)
    path('<int:pk>/delete/', views.event_delete, name='event_delete'),

    # URL สำหรับจัดการการลงทะเบียน
    path('<int:pk>/register/', views.event_register, name='event_register'),
    path('<int:pk>/unregister/', views.event_unregister, name='event_unregister'),

    # หน้าแสดงกิจกรรมที่ฉันสร้าง และกิจกรรมที่ฉันลงทะเบียน
    path('my-events/', views.MyOrganizedEventsView.as_view(),
         name='my_organized_events'),
    path('my-registrations/', views.MyRegistrationsView.as_view(),
         name='my_registrations'),

]
