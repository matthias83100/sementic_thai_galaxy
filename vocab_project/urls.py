from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('vocab_app.urls')), # Keeps /api/map-data/
    path('', include('vocab_app.urls')),     # Allows / for index
]
