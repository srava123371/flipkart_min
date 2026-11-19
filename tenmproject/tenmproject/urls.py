
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('kart/', include('kart.urls')),  # Include the URLs from the 'kart' app

]

