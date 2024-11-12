from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.home, name='home'), 
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('success/', views.success, name='success'),
    path('worker/', views.worker, name = 'worker'),
    path('logout/', views.logout, name='logout'),

]