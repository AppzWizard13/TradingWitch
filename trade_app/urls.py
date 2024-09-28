from django.urls import path
from . import views

urlpatterns = [
    path('configurations/', views.trading_configurations_list, name='trading_configurations_list'),
    path('configurations/create/', views.create_configuration, name='create_configuration'),
    path('configurations/edit/<int:config_id>/', views.create_configuration, name='edit_configuration'),
    path('configurations/get/<int:config_id>/', views.get_configuration, name='get_configuration'),
    path('configurations/<int:config_id>/delete/', views.delete_configuration, name='delete_configuration'),
]
