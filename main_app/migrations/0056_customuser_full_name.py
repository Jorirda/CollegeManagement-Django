# Generated by Django 3.1.1 on 2024-05-08 01:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0055_remove_customuser_contact_num'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='full_name',
            field=models.TextField(default=''),
        ),
    ]