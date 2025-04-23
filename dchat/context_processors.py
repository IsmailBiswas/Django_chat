from django.conf import settings


def provide_media_URL(request):
    return {"dchat_media_url": settings.DCHAT_MEDIA_URL}
