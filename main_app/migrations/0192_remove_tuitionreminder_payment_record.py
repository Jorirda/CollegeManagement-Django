# Generated by Django 3.1.1 on 2024-06-07 05:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0191_auto_20240605_1157'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tuitionreminder',
            name='payment_record',
        ),
    ]
