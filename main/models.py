import uuid
from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=[('user', 'User'), ('worker', 'Worker')], default='user')
    mypay_balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return self.user.username

class ServiceCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    
    def __str__(self):
        return self.name

class SubCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.ForeignKey(ServiceCategory, related_name='subcategories', on_delete=models.CASCADE)
    workers = models.ManyToManyField(UserProfile, related_name='subcategories', blank=True)  # Many-to-many relationship with workers

    def __str__(self):
        return self.name

class Testimonial(models.Model):
    rating = models.PositiveIntegerField(choices=[(i, str(i)) for i in range(1, 11)])
    comment = models.TextField()
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, related_name='testimonials')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='testimonials')

    def __str__(self):
        return f"Testimonial by {self.user.username} for {self.subcategory.name}"

class ServiceSession(models.Model):
    subcategory = models.ForeignKey('SubCategory', on_delete=models.CASCADE, related_name='sessions')
    session = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Session {self.session} for {self.subcategory.name} at {self.price}"
    
class MyPayTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('TopUp', 'Top Up'),
        ('ServicePayment', 'Service Payment'),
        ('Transfer', 'Transfer'),
        ('Withdrawal', 'Withdrawal'),
    ]

    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} by {self.user_profile.user.username}"

class ServiceOrder(models.Model):
    STATUS_CHOICES = [
        ('Looking for Nearby Worker', 'Looking for Nearby Worker'),
        ('Waiting for Worker to Depart', 'Waiting for Worker to Depart'),
        ('Worker Arrived at Location', 'Worker Arrived at Location'),
        ('Service in Progress', 'Service in Progress'),
        ('Order Completed', 'Order Completed'),
        ('Order Canceled', 'Order Canceled'),
    ]

    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='orders')
    worker = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_orders')
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE)
    order_date = models.DateField(auto_now_add=True)
    working_date = models.DateField(null=True, blank=True)  # Ensure null and blank are allowed
    session = models.CharField(max_length=100)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Looking for Nearby Worker')
    total_payment = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Order {self.id} - {self.status}"