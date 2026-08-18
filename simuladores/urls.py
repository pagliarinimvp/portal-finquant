from django.urls import path

from . import views

app_name = 'simuladores'

urlpatterns = [
    path('', views.SimuladoresIndexView.as_view(), name='index'),
    path('juros-compostos/', views.JurosCompostosView.as_view(), name='juros_compostos'),
    path('divida-cartao/', views.DividaCartaoView.as_view(), name='divida_cartao'),
    path('meta-financeira/', views.MetaFinanceiraView.as_view(), name='meta_financeira'),
]
