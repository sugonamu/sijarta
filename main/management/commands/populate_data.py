from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from main.models import UserProfile, ServiceCategory, SubCategory, ServiceOrder
from decimal import Decimal
from datetime import date

class Command(BaseCommand):
    help = 'Populate the database with initial data'

    def handle(self, *args, **kwargs):
        # Create Users
        user1, _ = User.objects.get_or_create(username="user1", defaults={"email": "user1@example.com"})
        user1.set_password("password")
        user1.save()
        worker1, _ = User.objects.get_or_create(username="worker1", defaults={"email": "worker1@example.com"})
        worker1.set_password("password")
        worker1.save()

        # Create UserProfiles
        user_profile, _ = UserProfile.objects.get_or_create(user=user1, defaults={"role": "user"})
        worker_profile, _ = UserProfile.objects.get_or_create(user=worker1, defaults={"role": "worker"})

        # Create Categories and Subcategories
        category, _ = ServiceCategory.objects.get_or_create(name="Home Services", description="All home services")
        subcat1, _ = SubCategory.objects.get_or_create(name="Plumbing", description="Fix plumbing issues", category=category)
        subcat2, _ = SubCategory.objects.get_or_create(name="Electrician", description="Electrical services", category=category)

        # Associate worker with subcategories
        worker_profile.subcategories.add(subcat1, subcat2)

        # Create Sample Orders
        ServiceOrder.objects.create(
            user=user_profile,
            subcategory=subcat1,
            order_date=date.today(),
            working_date=date.today(),
            session='Morning',
            status='Looking for Nearby Worker',
            total_payment=Decimal('100.00')
        )
        ServiceOrder.objects.create(
            user=user_profile,
            subcategory=subcat2,
            order_date=date.today(),
            working_date=date.today(),
            session='Afternoon',
            status='Waiting for Worker to Depart',
            worker=worker_profile,
            total_payment=Decimal('150.00')
        )
        ServiceOrder.objects.create(
            user=user_profile,
            subcategory=subcat1,
            order_date=date.today(),
            working_date=date.today(),
            session='Evening',
            status='Service in Progress',
            worker=worker_profile,
            total_payment=Decimal('200.00')
        )

        self.stdout.write(self.style.SUCCESS("Sample data created successfully."))
