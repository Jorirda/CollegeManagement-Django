# Generated by Django 3.1.1 on 2024-05-20 05:43

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0121_auto_20240520_1342'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feedbackteacher',
            name='created_at',
            field=models.DateField(default=django.utils.timezone.now),
        ),
    ]
