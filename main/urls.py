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
    path('subcategory/<int:subcategory_id>/', views.subcategory_detail, name='subcategory_detail'),
    path('join_service_category/<int:subcategory_id>/', views.join_service_category, name='join_service_category'),
    path('subcategory/<int:subcategory_id>/', views.subcategory_detail, name='subcategory_detail'),
    path('error/', views.error, name = 'error' ),
    path('discounts/', views.discounts, name = 'discounts'),
    path('managejob/', views.managejob, name = 'managejob'),
    path('manageorder/', views.manageorder, name = 'manageorder'),
    path('myorder/', views.myorder, name = 'myorder'),
    path('mypay/', views.mypay, name = 'mypay'),
    path('profile/', views.profile, name = 'profile'),
    

]