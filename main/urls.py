from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.login_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('success/', views.success_view, name='success'),
    path('subcategory/<str:subcategory_name>/', views.subcategory_user, name='subcategory_user'),
    path('mypay/', views.mypay_view, name='mypay'),
    path('mypay/transaction/', views.mypay_transaction_view, name='mypay_transaction'),
    path('logout/', views.logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('managejob/', views.managejob, name='managejob'),
    path('myorder/', views.myorder, name='myorder'),
    path('discounts/', views.discount, name='discounts'),
    path('manage_order_status/', views.manage_order_status, name='manage_order_status'),
]
