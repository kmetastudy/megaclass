# Generated by Django 5.2.1 on 2025-06-23 12:09

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('teacher', '0011_contenttypecategory_contenttype_category_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Contents_Template',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='제목')),
                ('page', models.TextField(help_text='HTML 형식의 콘텐츠', verbose_name='콘텐츠 페이지')),
                ('answer', models.TextField(blank=True, help_text='객관식/단답형의 경우 정답', null=True, verbose_name='정답')),
                ('meta_data', models.JSONField(blank=True, default=dict, verbose_name='메타데이터')),
                ('tags', models.JSONField(blank=True, default=dict, help_text='채점이나 평가 기준', verbose_name='태그/평가기준')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='생성일')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='수정일')),
                ('is_active', models.BooleanField(default=True, verbose_name='활성화')),
                ('is_public', models.BooleanField(default=True, help_text='다른 교사들도 사용할 수 있도록 공개', verbose_name='공개')),
                ('view_count', models.PositiveIntegerField(default=0, verbose_name='조회수')),
                ('content_category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='teacher.contenttypecategory', verbose_name='콘텐츠 타입 카테고리')),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='teacher.contenttype', verbose_name='콘텐츠 타입')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='생성자')),
            ],
            options={
                'verbose_name': '콘텐츠 템플릿',
                'verbose_name_plural': '콘텐츠 템플릿',
                'ordering': ['-created_at'],
            },
        ),
    ]
