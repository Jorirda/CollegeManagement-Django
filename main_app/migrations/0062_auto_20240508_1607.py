# Generated by Django 3.1.1 on 2024-05-08 08:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0061_auto_20240508_1559'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='student',
            name='grade',
        ),
        migrations.RemoveField(
            model_name='student',
            name='session',
        ),
        migrations.RemoveField(
            model_name='student',
            name='state',
        ),
    ]