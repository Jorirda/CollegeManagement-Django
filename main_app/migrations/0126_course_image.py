# Generated by Django 3.1.1 on 2024-05-21 06:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0125_customuser_total_semester'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='course_images/'),
        ),
    ]