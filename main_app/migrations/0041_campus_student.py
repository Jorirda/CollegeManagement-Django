# Generated by Django 3.1.1 on 2024-04-26 00:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0040_auto_20240425_1714'),
    ]

    operations = [
        migrations.AddField(
            model_name='campus',
            name='student',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, related_name='campuses', to='main_app.student'),
        ),
    ]
