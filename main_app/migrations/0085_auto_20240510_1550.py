# Generated by Django 3.1.1 on 2024-05-10 07:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0084_lessonhours'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Subject',
            new_name='Classes',
        ),
        migrations.RenameField(
            model_name='attendance',
            old_name='subject',
            new_name='classes',
        ),
        migrations.RenameField(
            model_name='classschedule',
            old_name='subject',
            new_name='classes',
        ),
        migrations.RenameField(
            model_name='studentresult',
            old_name='subject',
            new_name='classes',
        ),
    ]