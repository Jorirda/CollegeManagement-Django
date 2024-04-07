# Generated by Django 3.1.1 on 2024-04-03 08:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0004_learningrecord_paymentrecord_studentquery'),
    ]

    operations = [
        migrations.CreateModel(
            name='TeacherQuery',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gender', models.CharField(choices=[('M', 'Male'), ('F', 'Female')], max_length=1)),
                ('contact_number', models.CharField(max_length=100)),
                ('teaching_courses', models.CharField(max_length=100)),
                ('signing_form', models.CharField(max_length=100)),
                ('address', models.CharField(max_length=255)),
                ('course_hours_completed', models.IntegerField(default=0)),
                ('number_of_classes', models.IntegerField(default=0)),
                ('class_schedule_date', models.DateField()),
                ('class_schedule_course', models.CharField(max_length=100)),
                ('class_schedule_instructor', models.CharField(max_length=100)),
                ('class_schedule_starting_time', models.TimeField()),
                ('class_schedule_end_time', models.TimeField()),
                ('class_schedule_class', models.CharField(max_length=100)),
            ],
        ),
        migrations.AlterField(
            model_name='learningrecord',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main_app.course'),
        ),
        migrations.AlterField(
            model_name='learningrecord',
            name='remark',
            field=models.TextField(default=''),
        ),
        migrations.AlterField(
            model_name='paymentrecord',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main_app.course'),
        ),
        migrations.AlterField(
            model_name='paymentrecord',
            name='remark',
            field=models.TextField(default=''),
        ),
    ]