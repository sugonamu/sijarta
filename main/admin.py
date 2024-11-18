from django.contrib import admin
from .models import ServiceCategory, SubCategory, Testimonial, ServiceSession, Promo, Voucher, MyPayTransaction, ServiceOrder, UserProfile


class SubCategoryAdmin(admin.ModelAdmin):
    # Remove 'workers' from both the form and the displayed fields
    fields = ('name', 'description', 'category')  # Explicitly include only the fields you want to edit

    # Optional: Display workers in a read-only manner in the list view (but not editable)
    readonly_fields = ('workers_display',)

    def workers_display(self, obj):
        # Display a list of worker usernames
        return ", ".join([worker.user.username for worker in obj.workers.all()])
    workers_display.short_description = "Workers"

@admin.register(ServiceOrder)
class ServiceOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'worker', 'subcategory', 'status', 'total_payment', 'working_date')
    list_filter = ('status', 'working_date')
    search_fields = ('user__user__username', 'worker__user__username', 'subcategory__name')

admin.site.register(ServiceCategory)
admin.site.register(SubCategory, SubCategoryAdmin)  # Register with custom admin
admin.site.register(Testimonial)
admin.site.register(ServiceSession)
admin.site.register(Promo)
admin.site.register(Voucher)
admin.site.register(MyPayTransaction)