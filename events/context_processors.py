from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site


def social_login_providers(request):
    """ตรวจสอบว่ามีการตั้งค่า SocialApp สำหรับ Google หรือยัง"""
    google_login_enabled = False

    try:
        current_site = Site.objects.get_current(request)
    except Site.DoesNotExist:
        current_site = None

    if current_site is not None:
        google_login_enabled = SocialApp.objects.filter(
            provider='google',
            sites=current_site,
        ).exists()
    else:
        google_login_enabled = SocialApp.objects.filter(provider='google').exists()

    return {
        'google_login_enabled': google_login_enabled,
    }
