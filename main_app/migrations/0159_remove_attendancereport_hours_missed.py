# Generated by Django 3.1.1 on 2024-05-30 03:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0158_auto_20240528_1701'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='attendancereport',
            name='hours_missed',
        ),
    ]
