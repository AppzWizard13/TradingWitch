from . import views
from django.urls import path
from django.contrib import admin
from account.views import UserloginView, DashboardView, HomePageView

urlpatterns = [
    # # landing page
    # path('', views.HomePageView.as_view(), name='home'),
    # # login 
    # path('login/', views.UserloginView.as_view(), name = 'login'),
    # # dashboard 
    # path('dashboard', views.DashboardView.as_view(), name='dashboard'),











    
]