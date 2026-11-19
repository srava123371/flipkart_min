

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('home_page/', views.home, name='home_page'),
    path('checkout/', views.checkout, name='checkout'),
]
