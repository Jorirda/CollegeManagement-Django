# Generated by Django 3.1.1 on 2024-05-10 05:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0078_remove_paymentrecord_lesson_hours'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='paymentrecord',
            name='learning',
        ),
    ]
