# Generated by Django 3.1.1 on 2024-05-20 03:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0116_attendancereport_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendance',
            name='students',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='main_app.student'),
        ),
    ]