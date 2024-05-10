# Generated by Django 3.1.1 on 2024-05-10 05:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0080_remove_paymentrecord_class_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymentrecord',
            name='learning_record',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payment_record', to='main_app.learningrecord'),
        ),
    ]