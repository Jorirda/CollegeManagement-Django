# Generated by Django 3.1.1 on 2024-04-26 02:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0045_auto_20240426_1014'),
    ]

    operations = [
        migrations.AlterField(
            model_name='campus',
            name='teacher',
            field=models.ManyToManyField(related_name='campuses', to='main_app.Teacher'),
        ),
    ]
