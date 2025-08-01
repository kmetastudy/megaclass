# Generated by Django 5.2.1 on 2025-07-23 15:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('physical_education', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='papscategory',
            name='name',
            field=models.CharField(choices=[('CARDIO', '심폐지구력'), ('FLEXIBILITY', '유연성'), ('STRENGTH', '근력/근지구력'), ('AGILITY', '순발력'), ('BODY_FAT', '비만'), ('CARDIO_PRECISION', '심폐지구력정밀평가'), ('BODY_FAT_RATE', '체지방률평가'), ('POSTURE', '자세평가'), ('SELF_BODY', '자기신체평가')], max_length=30, unique=True),
        ),
    ]
