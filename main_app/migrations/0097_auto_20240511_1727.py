# Generated by Django 3.1.1 on 2024-05-11 09:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0096_paymentrecord_lesson_hours'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paymentrecord',
            name='lesson_hours',
            field=models.DecimalField(decimal_places=2, max_digits=10, null=True),
        ),
    ]