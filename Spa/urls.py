from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.conf import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', include('User.urls')),
    path('api/', include('api.urls')),
    path('customer/', include('customer.urls')),
    path('therapist/', include('therapist.urls')),
    path('chat/', include('chat.urls')),
    path('booking/', include('booking.urls')),
    path('admin_panel/', include('admin_panel.urls')),
]

def custom_page_not_found(request, exception):
    return HttpResponse(
        "<h1>404 Error</h1>"
        "<p>Looks like you took a wrong turn.</p>"
        "<p>But don’t worry, even the best explorers get lost sometimes!</p>"
        f"<p><a href='{settings.APP_URL}'>Click here to find your way home.</a></p>",
        status=404
    )

handler404 = custom_page_not_found