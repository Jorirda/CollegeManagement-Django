# Generated by Django 3.1.1 on 2024-04-07 04:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0006_auto_20240403_1641'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='is_staff',
        ),
        migrations.AddField(
            model_name='customuser',
            name='is_teacher',
            field=models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='teacher status'),
        ),
    ]