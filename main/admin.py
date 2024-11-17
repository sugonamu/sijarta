from django.contrib import admin
from .models import ServiceCategory, SubCategory,Testimonial,ServiceSession

admin.site.register(ServiceCategory)
admin.site.register(SubCategory)
admin.site.register(Testimonial)
admin.site.register(ServiceSession)