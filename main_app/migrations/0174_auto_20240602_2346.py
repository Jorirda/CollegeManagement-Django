# Generated by Django 3.1.1 on 2024-06-02 15:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0173_auto_20240602_2341'),
    ]

    operations = [
        migrations.AlterField(
            model_name='classschedule',
            name='lesson_hours',
            field=models.TimeField(null=True),
        ),
        migrations.AlterField(
            model_name='paymentrecord',
            name='lesson_hours',
            field=models.TimeField(null=True),
        ),
    ]