# Generated by Django 3.1.1 on 2024-04-26 01:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0042_campus_courses'),
    ]

    operations = [
        migrations.AlterField(
            model_name='campus',
            name='courses',
            field=models.ManyToManyField(default='', related_name='campuses', to='main_app.Course'),
        ),
    ]