# Generated by Django 3.1.1 on 2024-04-08 07:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0016_auto_20240408_1529'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentquery',
            name='date_of_birth',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='main_app.student'),
        ),
    ]