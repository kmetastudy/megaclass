#!/usr/bin/env python3
"""
PAPSRecord의 빈 문자열 evaluation_grade를 NULL로 정리하는 스크립트

사용법:
python scripts/clean_empty_evaluation_grades.py  # dry run 모드
python scripts/clean_empty_evaluation_grades.py --execute  # 실제 업데이트
"""

import os
import sys
import django

# Django 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import transaction
from physical_education.models import PAPSRecord


def clean_empty_grades(dry_run=True):
    """빈 문자열 evaluation_grade를 NULL로 정리"""
    
    print("=" * 60)
    print("PAPS 빈 문자열 등급 정리 스크립트")
    print("=" * 60)
    
    if dry_run:
        print("🔍 DRY RUN 모드: 실제 업데이트는 하지 않습니다.")
    else:
        print("⚡ 실행 모드: 실제 데이터를 업데이트합니다.")
    
    print()
    
    # 1. 현재 상태 조회
    print("📊 현재 evaluation_grade 상태 조회 중...")
    
    total_records = PAPSRecord.objects.count()
    
    # IntegerField이므로 빈 문자열은 이미 NULL로 변환되었을 수 있지만, 
    # 혹시 문제가 있는 데이터를 확인
    null_grades = PAPSRecord.objects.filter(evaluation_grade__isnull=True).count()
    valid_grades = PAPSRecord.objects.filter(evaluation_grade__isnull=False).count()
    
    print(f"📈 전체 PAPSRecord 수: {total_records:,}개")
    print(f"🎯 NULL인 등급: {null_grades:,}개")
    print(f"✅ 유효한 등급: {valid_grades:,}개")
    
    # 2. 범위를 벗어난 등급 확인
    print(f"\n🔍 등급 유효성 검사 중...")
    
    invalid_grades = PAPSRecord.objects.filter(
        evaluation_grade__isnull=False
    ).exclude(
        evaluation_grade__range=(1, 5)
    )
    
    invalid_count = invalid_grades.count()
    
    if invalid_count > 0:
        print(f"⚠️  유효하지 않은 등급 발견: {invalid_count:,}개")
        
        # 샘플 데이터 출력
        sample_invalid = invalid_grades[:5]
        for record in sample_invalid:
            print(f"   - Record ID: {record.id}, Grade: {record.evaluation_grade}")
    else:
        print("✅ 모든 등급이 유효한 범위(1-5)에 있습니다.")
    
    # 3. 정리 작업 수행
    if invalid_count > 0:
        print(f"\n🔄 잘못된 등급 데이터 정리 시작...")
        
        try:
            with transaction.atomic():
                if not dry_run:
                    # 잘못된 등급을 NULL로 설정
                    updated_count = invalid_grades.update(evaluation_grade=None)
                    print(f"✅ {updated_count:,}개의 잘못된 등급을 NULL로 설정했습니다.")
                else:
                    print(f"🔍 DRY RUN: {invalid_count:,}개의 잘못된 등급이 NULL로 설정될 예정입니다.")
                    
                    # dry_run 모드에서는 트랜잭션 롤백
                    if dry_run:
                        transaction.set_rollback(True)
        
        except Exception as e:
            print(f"❌ 정리 중 오류 발생: {str(e)}")
            return
    
    # 4. 최종 결과 출력
    print(f"\n{'='*60}")
    print("정리 결과")
    print(f"{'='*60}")
    
    if invalid_count > 0:
        if dry_run:
            print(f"🔍 DRY RUN 완료: {invalid_count:,}개의 잘못된 등급이 발견되었습니다.")
            print(f"💡 실제 정리를 하려면 --execute 옵션을 사용하세요.")
        else:
            print(f"🎉 정리 완료: {invalid_count:,}개의 잘못된 등급을 NULL로 설정했습니다.")
    else:
        print("✅ 정리할 데이터가 없습니다. 모든 등급이 유효합니다.")
    
    # 최종 상태 재확인
    if not dry_run and invalid_count > 0:
        final_null_grades = PAPSRecord.objects.filter(evaluation_grade__isnull=True).count()
        final_valid_grades = PAPSRecord.objects.filter(evaluation_grade__isnull=False).count()
        
        print(f"\n📊 정리 후 상태:")
        print(f"🎯 NULL인 등급: {final_null_grades:,}개")
        print(f"✅ 유효한 등급: {final_valid_grades:,}개")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='PAPSRecord 빈 문자열 등급 정리')
    parser.add_argument('--execute', action='store_true', help='실제 업데이트 실행 (기본: dry run)')
    
    args = parser.parse_args()
    
    clean_empty_grades(dry_run=not args.execute)