# Generated by Django 3.1.1 on 2024-05-27 02:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0147_classschedule_day_of_week'),
    ]

    operations = [
        migrations.AddField(
            model_name='notificationteacher',
            name='classroom_performance',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='notificationteacher',
            name='status_pictures',
            field=models.ImageField(blank=True, null=True, upload_to='status_pictures/'),
        ),
    ]