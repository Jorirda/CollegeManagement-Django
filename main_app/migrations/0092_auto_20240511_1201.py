# Generated by Django 3.1.1 on 2024-05-11 04:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0091_auto_20240511_1043'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='level_end',
            field=models.IntegerField(default=4),
        ),
        migrations.AddField(
            model_name='course',
            name='level_start',
            field=models.IntegerField(default=1),
        ),
    ]