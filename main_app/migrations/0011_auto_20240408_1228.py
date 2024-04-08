# Generated by Django 3.1.1 on 2024-04-08 04:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0010_auto_20240408_1105'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentquery',
            name='class_ending_time',
            field=models.TimeField(null=True),
        ),
        migrations.AddField(
            model_name='studentquery',
            name='class_name',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='studentquery',
            name='class_starting_time',
            field=models.TimeField(null=True),
        ),
        migrations.AddField(
            model_name='studentquery',
            name='date',
            field=models.DateField(null=True),
        ),
        migrations.AddField(
            model_name='studentquery',
            name='instructor',
            field=models.CharField(default='', max_length=100),
        ),
    ]
