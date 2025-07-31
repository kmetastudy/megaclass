#!/usr/bin/env python3
"""
기존 PAPSRecord 데이터의 evaluation_grade 계산 및 업데이트 스크립트

사용법:
python scripts/update_existing_paps_grades.py  # dry run 모드
python scripts/update_existing_paps_grades.py --execute  # 실제 업데이트
"""

import os
import sys
import django

# Django 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import transaction
from django.db.models import Q
from physical_education.models import PAPSRecord, PAPSActivity
from physical_education.utils import calculate_paps_grade


def update_existing_grades(dry_run=True):
    """기존 PAPSRecord의 등급 계산 및 업데이트"""
    
    print("=" * 60)
    print("PAPS 기존 기록 등급 계산 스크립트")
    print("=" * 60)
    
    if dry_run:
        print("🔍 DRY RUN 모드: 실제 업데이트는 하지 않습니다.")
    else:
        print("⚡ 실행 모드: 실제 데이터를 업데이트합니다.")
    
    print()
    
    # 1. 처리 대상 레코드 조회
    print("📊 처리 대상 레코드 조회 중...")
    
    # measurement_data가 빈 dict가 아니고, evaluation_grade가 없는 레코드
    # IntegerField 마이그레이션 과정에서 빈 문자열이 남아있을 수 있으므로 두 조건 모두 확인
    target_records = PAPSRecord.objects.filter(
        ~Q(measurement_data={}),  # 빈 dict가 아닌 경우
    ).extra(
        where=["evaluation_grade IS NULL OR evaluation_grade = ''"]
    ).select_related()
    
    total_records = PAPSRecord.objects.count()
    target_count = target_records.count()
    
    print(f"📈 전체 PAPSRecord 수: {total_records:,}개")
    print(f"🎯 처리 대상 레코드 수: {target_count:,}개")
    
    if target_count == 0:
        print("✅ 처리할 레코드가 없습니다.")
        return
    
    # 2. PAPSActivity 정보 조회
    print("\n📋 활동별 평가 기준 조회 중...")
    
    activities = {
        str(activity.id): activity 
        for activity in PAPSActivity.objects.all()
    }
    
    required_activities = [
        activity for activity in activities.values() 
        if activity.evaluation_criteria
    ]
    
    print(f"📊 전체 활동 수: {len(activities)}개")
    print(f"📏 평가 기준이 있는 활동: {len(required_activities)}개")
    
    # 3. 레코드별 처리
    print(f"\n🔄 레코드 처리 시작...")
    
    stats = {
        'processed': 0,
        'calculated': 0,
        'no_criteria': 0,
        'missing_field': 0,
        'errors': 0
    }
    
    processed_samples = []
    error_details = []
    
    try:
        with transaction.atomic():
            for i, record in enumerate(target_records, 1):
                if i % 100 == 0:
                    print(f"   진행률: {i:,}/{target_count:,} ({100*i/target_count:.1f}%)")
                
                try:
                    # 활동 정보 조회
                    activity = activities.get(str(record.activity_id))
                    if not activity:
                        error_details.append({
                            'record_id': str(record.id),
                            'error': 'Activity not found',
                            'activity_id': str(record.activity_id)
                        })
                        stats['errors'] += 1
                        continue
                    
                    # 평가 기준이 있는 활동인지 확인
                    if not activity.evaluation_criteria:
                        stats['no_criteria'] += 1
                        continue
                    
                    # calculation_field 확인
                    calculation_field = activity.evaluation_criteria.get('calculation_field')
                    if not calculation_field:
                        error_details.append({
                            'record_id': str(record.id),
                            'error': 'No calculation_field in evaluation_criteria',
                            'activity_name': activity.get_name_display()
                        })
                        stats['errors'] += 1
                        continue
                    
                    # measurement_data에 필요한 필드가 있는지 확인
                    measurement_value = record.measurement_data.get(calculation_field)
                    if measurement_value is None:
                        stats['missing_field'] += 1
                        continue
                    
                    # 등급 계산
                    grade_result = calculate_paps_grade(
                        activity=activity,
                        measurement_data=record.measurement_data,
                        student_grade=record.student_grade
                    )
                    
                    if 'error' in grade_result:
                        error_details.append({
                            'record_id': str(record.id),
                            'error': f"Grade calculation error: {grade_result.get('error', 'Unknown error')}",
                            'activity_name': activity.get_name_display(),
                            'calculation_field': calculation_field,
                            'measurement_value': measurement_value,
                            'student_grade': record.student_grade
                        })
                        stats['errors'] += 1
                        continue
                    
                    # 등급 추출 (임시로 male_grade 사용)
                    grade_code = grade_result.get('male_grade_code')
                    evaluation_grade = None
                    
                    if grade_code and grade_code.startswith('grade_'):
                        try:
                            evaluation_grade = int(grade_code.split('_')[1])
                        except (IndexError, ValueError) as e:
                            error_details.append({
                                'record_id': str(record.id),
                                'error': f"Grade code parsing error: {str(e)}",
                                'activity_name': activity.get_name_display(),
                                'grade_code': grade_code
                            })
                            stats['errors'] += 1
                            continue
                    else:
                        # grade_code가 None인 경우, 범위 밖 값으로 추정하여 경계값 설정
                        if grade_result.get('male_grade') is None and grade_result.get('female_grade') is None:
                            # 측정값이 범위를 벗어난 경우 경계값으로 등급 설정
                            criteria = activity.evaluation_criteria.get('criteria', {})
                            student_grade_str = f"초{record.student_grade}" if record.student_grade <= 6 else f"중{record.student_grade - 6}" if record.student_grade <= 9 else f"고{record.student_grade - 9}"
                            
                            # 성별별 기준 확인 (임시로 male 사용)
                            gender_criteria = criteria.get('male', {}).get(student_grade_str, {})
                            if not gender_criteria:
                                gender_criteria = criteria.get('all', {}).get('all_grades', {})
                            
                            if gender_criteria:
                                # 각 등급의 범위를 확인하여 측정값이 어느 쪽 경계를 벗어났는지 판단
                                grade_ranges = {}
                                for grade_key, range_info in gender_criteria.items():
                                    if isinstance(range_info, dict):
                                        min_val = range_info.get('min', float('-inf'))
                                        max_val = range_info.get('max', float('inf'))
                                        grade_ranges[grade_key] = (min_val, max_val)
                                
                                if grade_ranges:
                                    # 가장 낮은 값의 최솟값과 가장 높은 값의 최댓값 찾기
                                    all_mins = [r[0] for r in grade_ranges.values() if r[0] != float('-inf')]
                                    all_maxs = [r[1] for r in grade_ranges.values() if r[1] != float('inf')]
                                    
                                    if all_mins and all_maxs:
                                        overall_min = min(all_mins)
                                        overall_max = max(all_maxs)
                                        
                                        # lower_better 활동인지 확인
                                        is_lower_better = activity.evaluation_criteria.get('calculation_method') == 'lower_better'
                                        
                                        if is_lower_better:
                                            # 낮을수록 좋은 활동 (시간, 거리 등)
                                            if measurement_value < overall_min:
                                                evaluation_grade = 1  # 최고 등급
                                            elif measurement_value > overall_max:
                                                evaluation_grade = 5  # 최저 등급
                                        else:
                                            # 높을수록 좋은 활동 (횟수, 거리 등)
                                            if measurement_value < overall_min:
                                                evaluation_grade = 5  # 최저 등급
                                            elif measurement_value > overall_max:
                                                evaluation_grade = 1  # 최고 등급
                                
                                # 경계값 설정이 성공한 경우
                                if evaluation_grade:
                                    error_details.append({
                                        'record_id': str(record.id),
                                        'error': f"Out of range value - assigned boundary grade: {evaluation_grade}",
                                        'activity_name': activity.get_name_display(),
                                        'measurement_value': measurement_value,
                                        'boundary_reason': f"Value {measurement_value} outside range [{overall_min}-{overall_max}]"
                                    })
                        
                        # 여전히 등급을 설정하지 못한 경우
                        if evaluation_grade is None:
                            error_details.append({
                                'record_id': str(record.id),
                                'error': f"Could not determine grade: {grade_code}",
                                'activity_name': activity.get_name_display(),
                                'grade_result': grade_result
                            })
                            stats['errors'] += 1
                            continue
                    
                    # 등급이 성공적으로 설정된 경우
                    if evaluation_grade:
                        # 샘플 데이터 수집 (처음 5개)
                        if len(processed_samples) < 5:
                            processed_samples.append({
                                'activity_name': activity.get_name_display(),
                                'calculation_field': calculation_field,
                                'measurement_value': measurement_value,
                                'grade': evaluation_grade,
                                'student_grade': record.student_grade
                            })
                        
                        if not dry_run:
                            record.evaluation_grade = evaluation_grade
                            record.save(update_fields=['evaluation_grade'])
                        
                        stats['calculated'] += 1
                    
                    stats['processed'] += 1
                    
                except Exception as e:
                    error_details.append({
                        'record_id': str(record.id),
                        'error': f"Unexpected error: {str(e)}",
                        'activity_id': str(record.activity_id) if record.activity_id else 'None'
                    })
                    print(f"   ❌ 레코드 {record.id} 처리 오류: {str(e)}")
                    stats['errors'] += 1
            
            if dry_run:
                # dry_run 모드에서는 트랜잭션 롤백
                transaction.set_rollback(True)
    
    except Exception as e:
        print(f"❌ 처리 중 오류 발생: {str(e)}")
        return
    
    # 4. 결과 출력
    print(f"\n{'='*60}")
    print("처리 결과")
    print(f"{'='*60}")
    print(f"📊 총 처리된 레코드: {stats['processed']:,}개")
    print(f"✅ 등급 계산 성공: {stats['calculated']:,}개")
    print(f"⚠️  평가 기준 없음: {stats['no_criteria']:,}개")
    print(f"⚠️  필수 필드 누락: {stats['missing_field']:,}개")
    print(f"❌ 오류 발생: {stats['errors']:,}개")
    
    if processed_samples:
        print(f"\n📋 처리된 샘플 데이터:")
        for i, sample in enumerate(processed_samples, 1):
            print(f"   {i}. {sample['activity_name']}")
            print(f"      - 필드: {sample['calculation_field']} = {sample['measurement_value']}")
            print(f"      - 학년: {sample['student_grade']} → 등급: {sample['grade']}")
    
    if error_details:
        print(f"\n❌ 오류 상세 정보:")
        for error in error_details:
            print(f"   • Record ID: {error['record_id']}")
            print(f"     오류: {error['error']}")
            if 'activity_name' in error:
                print(f"     활동: {error['activity_name']}")
            if 'activity_id' in error:
                print(f"     Activity ID: {error['activity_id']}")
            if 'calculation_field' in error:
                print(f"     필드: {error['calculation_field']} = {error.get('measurement_value', 'N/A')}")
            if 'student_grade' in error:
                print(f"     학년: {error['student_grade']}")
            if 'grade_code' in error:
                print(f"     Grade Code: {error['grade_code']}")
            if 'grade_result' in error:
                print(f"     Grade Result: {error['grade_result']}")
            if 'boundary_reason' in error:
                print(f"     경계값 설정 이유: {error['boundary_reason']}")
            print()
    
    if dry_run:
        print(f"\n💡 실제 업데이트를 하려면 --execute 옵션을 사용하세요.")
    else:
        print(f"\n🎉 등급 업데이트가 완료되었습니다!")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='기존 PAPSRecord 등급 계산 및 업데이트')
    parser.add_argument('--execute', action='store_true', help='실제 업데이트 실행 (기본: dry run)')
    
    args = parser.parse_args()
    
    update_existing_grades(dry_run=not args.execute)