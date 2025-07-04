# Generated by Django 5.2.1 on 2025-06-01 09:10

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teacher', '0003_contents_answer_alter_contents_difficulty_level_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='contents',
            options={'ordering': ['-created_at'], 'verbose_name': '콘텐츠', 'verbose_name_plural': '콘텐츠'},
        ),
        migrations.RemoveField(
            model_name='contents',
            name='difficulty_level',
        ),
        migrations.RemoveField(
            model_name='contents',
            name='estimated_time',
        ),
        migrations.RemoveField(
            model_name='contents',
            name='is_public',
        ),
        migrations.RemoveField(
            model_name='contents',
            name='view_count',
        ),
        migrations.AddField(
            model_name='contents',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='활성화'),
        ),
        migrations.AddField(
            model_name='contents',
            name='meta_data',
            field=models.JSONField(blank=True, default=dict, verbose_name='메타데이터'),
        ),
        migrations.AlterField(
            model_name='contents',
            name='answer',
            field=models.TextField(blank=True, help_text='객관식/단답형의 경우 정답', null=True, verbose_name='정답'),
        ),
        migrations.AlterField(
            model_name='contents',
            name='content_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='teacher.contenttype', verbose_name='콘텐츠 타입'),
        ),
        migrations.AlterField(
            model_name='contents',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='생성자'),
        ),
        migrations.AlterField(
            model_name='contents',
            name='page',
            field=models.TextField(help_text='HTML 형식의 콘텐츠', verbose_name='콘텐츠 페이지'),
        ),
        migrations.AlterField(
            model_name='contents',
            name='tags',
            field=models.JSONField(blank=True, default=dict, help_text='채점이나 평가 기준', verbose_name='태그/평가기준'),
        ),
    ]
