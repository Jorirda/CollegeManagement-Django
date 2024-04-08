# Generated by Django 3.1.1 on 2024-04-07 07:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0007_auto_20240407_1230'),
    ]

    operations = [
        migrations.CreateModel(
            name='Institution',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.RemoveField(
            model_name='learningrecord',
            name='instructor',
        ),
        migrations.RemoveField(
            model_name='learningrecord',
            name='name',
        ),
        migrations.AddField(
            model_name='learningrecord',
            name='student',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.DO_NOTHING, to='main_app.student'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='learningrecord',
            name='teacher',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='main_app.teacher'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='learningrecord',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='paymentrecord',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.CreateModel(
            name='ClassSchedule',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('lesson_unit_price', models.CharField(max_length=100)),
                ('class_time', models.CharField(max_length=100)),
                ('remark', models.TextField(default='')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main_app.course')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='main_app.subject')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main_app.teacher')),
            ],
        ),
        migrations.CreateModel(
            name='Campus',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('institution', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main_app.institution')),
            ],
        ),
    ]