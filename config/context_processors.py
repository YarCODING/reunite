from django.conf import settings

def environment_status(request):
    return {
        'IS_DEVELOPMENT': settings.DEBUG
    }