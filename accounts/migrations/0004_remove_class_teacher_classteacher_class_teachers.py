# Generated by Django 5.2.1 on 2025-06-08 02:19

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_alter_class_teacher'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='class',
            name='teacher',
        ),
        migrations.CreateModel(
            name='ClassTeacher',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('admin_teacher', '총괄 교사'), ('main_teacher', '담임 교사'), ('subject_teacher', '교과 교사'), ('assistant', '부담임/보조 교사'), ('etc', '기타')], default='main_teacher', max_length=20, verbose_name='역할')),
                ('class_instance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.class', verbose_name='학급')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.teacher', verbose_name='교사')),
            ],
            options={
                'verbose_name': '학급별 교사',
                'verbose_name_plural': '학급별 교사 목록',
                'unique_together': {('class_instance', 'teacher')},
            },
        ),
        migrations.AddField(
            model_name='class',
            name='teachers',
            field=models.ManyToManyField(related_name='classes', through='accounts.ClassTeacher', to='accounts.teacher', verbose_name='담당 교사들'),
        ),
    ]
