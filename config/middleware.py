from django.contrib.auth import get_user_model

class SaveUserLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if response.status_code < 400 and request.user.is_authenticated and hasattr(request, 'LANGUAGE_CODE'):
            try:
                profile = getattr(request.user, 'profile', None)
                
                if profile:
                    short_lang = request.LANGUAGE_CODE[:2]
                    
                    if profile.lang != short_lang:
                        profile.lang = short_lang
                        profile.save(update_fields=['lang'])
                        
            except Exception:
                pass

        return response