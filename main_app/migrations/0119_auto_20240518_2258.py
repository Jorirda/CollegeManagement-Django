# Generated by Django 3.1.1 on 2024-05-18 14:58

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0118_auto_20240518_1318'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student',
            name='admin',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
