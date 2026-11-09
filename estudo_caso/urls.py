from django.urls import path

from . import views

app_name = 'estudo_caso'

urlpatterns = [
    path('', views.PerguntarView.as_view(), name='index'),
    path('analise/', views.AnaliseView.as_view(), name='analise'),
    path('status/<str:chave>/', views.StatusView.as_view(), name='status'),
    path('pdf/', views.PdfView.as_view(), name='pdf'),
]
