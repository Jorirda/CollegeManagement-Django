# Generated by Django 3.1.1 on 2024-04-28 05:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0051_customuser_campus'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='campus',
            field=models.CharField(default='', max_length=100),
        ),
    ]
