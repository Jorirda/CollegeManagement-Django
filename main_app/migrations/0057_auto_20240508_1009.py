# Generated by Django 3.1.1 on 2024-05-08 02:09

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0056_customuser_full_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='admin',
            name='admin',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
