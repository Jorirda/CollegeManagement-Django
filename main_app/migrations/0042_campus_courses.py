# Generated by Django 3.1.1 on 2024-04-26 01:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0041_campus_student'),
    ]

    operations = [
        migrations.AddField(
            model_name='campus',
            name='courses',
            field=models.ManyToManyField(related_name='campuses', to='main_app.Course'),
        ),
    ]