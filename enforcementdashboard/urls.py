from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/ice-arrests/', permanent=False)),  # root → /ice-arrests/
    path('ice-arrests/', include('dashboards.urls')),               # include app urls here
]
