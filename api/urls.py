from django.urls import path
from . import views

urlpatterns = [
    path('pictures/', views.pictures_view, name='pictures'),
]