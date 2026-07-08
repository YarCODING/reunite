from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from users.views import profile_view
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("posts.urls")),
    path('accounts/', include('allauth.urls')),
    path('profile/', include('users.urls')),
    path("chats/", include("chats.urls")),
    path('payment/', include('payments.urls')),
    path('subscription/', include('subscription.urls')),
    path('@<username>/', profile_view, name='profile')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)