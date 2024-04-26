# Generated by Django 3.1.1 on 2024-04-25 09:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0039_auto_20240425_1614'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='campus',
            name='students',
        ),
        migrations.RemoveField(
            model_name='campus',
            name='teachers',
        ),
        migrations.AddField(
            model_name='campus',
            name='teacher',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, related_name='campuses', to='main_app.teacher'),
        ),
    ]