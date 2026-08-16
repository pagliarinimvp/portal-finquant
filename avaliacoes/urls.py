from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = 'avaliacoes'

urlpatterns = [
    path('', views.AvaliacaoCreateView.as_view(), name='avaliar'),
    path('obrigado/', TemplateView.as_view(template_name='avaliacoes/obrigado.html'), name='obrigado'),
]
