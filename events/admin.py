from django.contrib import admin
from .models import Event, Registration


class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'organizer', 'start_datetime',
                    'location', 'max_participants', 'category')
    list_filter = ('start_datetime', 'organizer', 'category')
    search_fields = ('title', 'description', 'location')


class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'registered_at', 'status')
    list_filter = ('event', 'status')
    search_fields = ('user__username', 'event__title')


# ลงทะเบียน Model ของเรากับหน้า Admin
admin.site.register(Event, EventAdmin)
admin.site.register(Registration, RegistrationAdmin)
