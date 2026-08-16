from django.urls import path

from . import views

app_name = 'conteudo'

urlpatterns = [
    path('', views.ArtigoListView.as_view(), name='lista'),
    path('<slug:slug>/', views.ArtigoDetailView.as_view(), name='detalhe'),
]
