# Generated by Django 3.1.1 on 2024-05-10 03:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0075_auto_20240510_1027'),
    ]

    operations = [
        migrations.AlterField(
            model_name='learningrecord',
            name='lesson_hours',
            field=models.TextField(default=''),
        ),
        migrations.DeleteModel(
            name='RefundRecord',
        ),
    ]
