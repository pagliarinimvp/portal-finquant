from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('sobre/', views.SobreView.as_view(), name='sobre'),
    path('saude/', views.saude, name='saude'),
]
