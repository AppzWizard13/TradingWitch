from . import views
from django.urls import path
from django.contrib import admin
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('options-chain-view/<str:slug>/', views.OptionChainView.as_view(), name='options_chain_view'),
    path('update-data-instance/', views.update_data_instance, name='update_data_instance'),

    path('close_all_positions', views.close_all_positions, name='close_all_positions'),
    path('get_open_temp_data/', views.get_open_temp_data, name='get_open_temp_data'),

    path('instant-buy-order/', views.instantBuyOrderWithSL, name='instant_buy_order'),














    
]