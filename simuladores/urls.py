from django.urls import path

from . import views

app_name = 'simuladores'

urlpatterns = [
    path('juros-compostos/', views.JurosCompostosView.as_view(), name='juros_compostos'),
]
