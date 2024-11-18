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
    path('mypay/', views.mypay, name='mypay'),
    path('mypay/transactions/', views.mypay_transactions, name='mypay_transactions'),
    path('service_jobs/', views.service_jobs, name='service_jobs'),
    path('service_job_status/', views.service_job_status, name='service_job_status'),
    path('transact/', views.transact, name='transact'),
    path('mypay_transactions/', views.mypay_transactions, name='mypay_transactions'),
    path('managejob/', views.managejob, name='managejob'),
    path('accept_order/<int:order_id>/', views.accept_order, name='accept_order'),
    path('manage_order_status/', views.manage_order_status, name='manage_order_status'),
    path('add_testimony/<int:subcategory_id>/', views.AddTestimonial, name='add_testimonial'),
    path('worker-profile/', views.worker_profile, name='worker_profile'),
    path('booking-service/', views.booking_service, name='booking_service')
]