# Generated by Django 3.1.1 on 2024-04-24 06:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0033_auto_20240424_1407'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='grade',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='customuser',
            name='school',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]