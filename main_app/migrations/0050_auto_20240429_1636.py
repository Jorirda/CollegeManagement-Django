# Generated by Django 3.1.1 on 2024-04-29 08:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0049_auto_20240429_1052'),
    ]

    operations = [
        migrations.AddField(
            model_name='learningrecord',
            name='campus',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='main_app.campus'),
        ),
        migrations.AddField(
            model_name='learningrecord',
            name='institution',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='main_app.institution'),
        ),
    ]