# Generated by Django 3.1.1 on 2024-04-28 03:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0048_auto_20240426_1614'),
    ]

    operations = [
        migrations.AlterField(
            model_name='teacher',
            name='campus',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='main_app.campus'),
        ),
    ]
