# Generated by Django 3.1.1 on 2024-05-26 04:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0142_remove_classschedule_lesson_unit_price'),
    ]

    operations = [
        migrations.RenameField(
            model_name='session',
            old_name='end_year',
            new_name='end_date',
        ),
        migrations.RenameField(
            model_name='session',
            old_name='start_year',
            new_name='start_date',
        ),
    ]
