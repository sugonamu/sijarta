import uuid
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=[('user', 'User'), ('worker', 'Worker')], default='user')

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
    
    def __str__(self):
        return self.name

class Testimonial(models.Model):
    rating = models.PositiveIntegerField(choices=[(i, str(i)) for i in range(1, 11)])
    comment = models.TextField()
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE, related_name='testimonials')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='testimonials')

    def __str__(self):
        return f"Testimonial by {self.user.username} for {self.subcategory.name}"