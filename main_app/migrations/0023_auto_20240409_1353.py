# Generated by Django 3.1.1 on 2024-04-09 05:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0022_auto_20240409_1337'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='studentquery',
            name='admin',
        ),
        migrations.RemoveField(
            model_name='studentquery',
            name='completed_hours',
        ),
        migrations.RemoveField(
            model_name='studentquery',
            name='learning_records',
        ),
        migrations.RemoveField(
            model_name='studentquery',
            name='num_of_classes',
        ),
        migrations.RemoveField(
            model_name='studentquery',
            name='paid_class_hours',
        ),
        migrations.RemoveField(
            model_name='studentquery',
            name='payment_records',
        ),
        migrations.RemoveField(
            model_name='studentquery',
            name='refund',
        ),
        migrations.RemoveField(
            model_name='studentquery',
            name='registered_courses',
        ),
        migrations.RemoveField(
            model_name='studentquery',
            name='remaining_hours',
        ),
        migrations.RemoveField(
            model_name='studentquery',
            name='student_records',
        ),
        migrations.AddField(
            model_name='studentquery',
            name='course',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='main_app.course'),
        ),
        migrations.AddField(
            model_name='studentquery',
            name='date',
            field=models.DateField(null=True),
        ),
    ]
