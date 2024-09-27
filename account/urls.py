from . import views
from django.urls import path
from django.contrib import admin
from account.views import UserloginView, DashboardView, HomePageView
from django.contrib.auth import views as auth_views

urlpatterns = [
    # landing page
    path('', views.HomePageView.as_view(), name='home'),
    # login 
    path('login/', views.UserloginView.as_view(), name = 'login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),  # Add this line
    # dashboard 
    path('dashboard', views.DashboardView.as_view(), name='dashboard'),
    # auth code view  
    path('authcodes/', views.AuthCodeListView.as_view(), name='authcode-list'),


    # path('api/login/', views.login_view, name='api_login'),
    # path('api/logout/', views.api_logout, name='api_logout'),
    # path('api/csrf-token/', views.csrf_token_view, name='csrf-token'),
    # path('api/fetch-trade-configurations/', views.fetch_trade_configurations, name='fetch_trade_configurations'),











    
]