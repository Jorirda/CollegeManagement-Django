# Generated by Django 3.1.1 on 2024-05-24 05:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0140_auto_20240524_0936'),
    ]

    operations = [
        migrations.AlterField(
            model_name='summaryteacher',
            name='summary',
            field=models.TextField(verbose_name='Summary'),
        ),
    ]
