# Generated by Django 3.1.1 on 2024-04-25 03:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0035_auto_20240425_1041'),
    ]

    operations = [
        migrations.RenameField(
            model_name='customuser',
            old_name='school',
            new_name='campus',
        ),
    ]
