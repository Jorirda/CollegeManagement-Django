# Generated by Django 3.1.1 on 2024-06-03 01:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0177_auto_20240603_0052'),
    ]

    operations = [
        migrations.AlterField(
            model_name='classschedule',
            name='lesson_hours',
            field=models.DurationField(null=True),
        ),
    ]