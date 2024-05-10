# Generated by Django 3.1.1 on 2024-05-10 01:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0072_remove_paymentrecord_lesson_hours'),
    ]

    operations = [
        migrations.CreateModel(
            name='RefundRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_of_birth', models.DateField()),
                ('full_name', models.CharField(max_length=255)),
                ('total_duration_of_lesson', models.DecimalField(decimal_places=2, help_text='Total duration in hours', max_digits=5)),
                ('hours_spent_learning', models.DecimalField(decimal_places=2, max_digits=5)),
                ('hours_remaining', models.DecimalField(decimal_places=2, max_digits=5)),
                ('lesson_unit_price', models.DecimalField(decimal_places=2, help_text='Unit price in the local currency', max_digits=10)),
                ('amount_to_be_refunded', models.DecimalField(decimal_places=2, max_digits=10)),
                ('amount_refunded', models.DecimalField(decimal_places=2, max_digits=10)),
                ('reason_for_refund', models.TextField()),
                ('courses', models.ManyToManyField(to='main_app.Course')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='refund_records', to='main_app.student')),
            ],
        ),
    ]