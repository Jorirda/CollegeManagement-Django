# Generated by Django 3.1.1 on 2024-05-11 08:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0094_auto_20240511_1558'),
    ]

    operations = [
        migrations.AlterField(
            model_name='learningrecord',
            name='lesson_hours',
            field=models.CharField(max_length=10, null=True),
        ),
    ]