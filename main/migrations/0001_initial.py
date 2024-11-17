# Generated by Django 5.1.1 on 2024-11-17 19:00

import django.db.models.deletion
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ServiceCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='SubCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subcategories', to='main.servicecategory')),
            ],
        ),
        migrations.CreateModel(
            name='ServiceSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session', models.IntegerField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('subcategory', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='main.subcategory')),
            ],
        ),
        migrations.CreateModel(
            name='Testimonial',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveIntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'), (6, '6'), (7, '7'), (8, '8'), (9, '9'), (10, '10')])),
                ('comment', models.TextField()),
                ('subcategory', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='testimonials', to='main.subcategory')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='testimonials', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('user', 'User'), ('worker', 'Worker')], default='user', max_length=10)),
                ('mypay_balance', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='subcategory',
            name='workers',
            field=models.ManyToManyField(blank=True, related_name='subcategories', to='main.userprofile'),
        ),
        migrations.CreateModel(
            name='ServiceOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_date', models.DateField(auto_now_add=True)),
                ('working_date', models.DateField(blank=True, null=True)),
                ('session', models.CharField(max_length=100)),
                ('status', models.CharField(choices=[('Looking for Nearby Worker', 'Looking for Nearby Worker'), ('Waiting for Worker to Depart', 'Waiting for Worker to Depart'), ('Worker Arrived at Location', 'Worker Arrived at Location'), ('Service in Progress', 'Service in Progress'), ('Order Completed', 'Order Completed'), ('Order Canceled', 'Order Canceled')], default='Looking for Nearby Worker', max_length=50)),
                ('total_payment', models.DecimalField(decimal_places=2, max_digits=10)),
                ('subcategory', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.subcategory')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='main.userprofile')),
                ('worker', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_orders', to='main.userprofile')),
            ],
        ),
        migrations.CreateModel(
            name='MyPayTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_type', models.CharField(choices=[('TopUp', 'Top Up'), ('ServicePayment', 'Service Payment'), ('Transfer', 'Transfer'), ('Withdrawal', 'Withdrawal')], max_length=20)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('user_profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='main.userprofile')),
            ],
        ),
    ]
