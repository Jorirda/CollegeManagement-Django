# Generated by Django 3.1.1 on 2024-04-10 02:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0024_auto_20240409_1436'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='studentquery',
            name='course',
        ),
        migrations.RemoveField(
            model_name='studentquery',
            name='date',
        ),
        migrations.AddField(
            model_name='studentquery',
            name='admin',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='studentquery',
            name='completed_hours',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='studentquery',
            name='learning_records',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='main_app.learningrecord'),
        ),
        migrations.AddField(
            model_name='studentquery',
            name='num_of_classes',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='studentquery',
            name='paid_class_hours',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='studentquery',
            name='payment_records',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='main_app.paymentrecord'),
        ),
        migrations.AddField(
            model_name='studentquery',
            name='refund',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='studentquery',
            name='registered_courses',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='studentquery',
            name='remaining_hours',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='studentquery',
            name='student_records',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='main_app.student'),
        ),
    ]
