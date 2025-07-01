from django.core.management.base import BaseCommand
from ncs.models import NCSCompetency

class Command(BaseCommand):
    help = 'NCS 기본 역량 데이터 초기화'
    
    def handle(self, *args, **options):
        competencies = [
            # 의사소통능력
            {'code': 'COM001', 'main_category': '의사소통능력', 'sub_category': '문서이해능력', 'competency_name': '문서이해능력', 'level': 3},
            {'code': 'COM002', 'main_category': '의사소통능력', 'sub_category': '문서작성능력', 'competency_name': '문서작성능력', 'level': 3},
            {'code': 'COM003', 'main_category': '의사소통능력', 'sub_category': '경청능력', 'competency_name': '경청능력', 'level': 3},
            {'code': 'COM004', 'main_category': '의사소통능력', 'sub_category': '의사표현능력', 'competency_name': '의사표현능력', 'level': 3},
            {'code': 'COM005', 'main_category': '의사소통능력', 'sub_category': '기초외국어능력', 'competency_name': '기초외국어능력', 'level': 3},

            # 자원관리 능력
            {'code': 'RES001', 'main_category': '자원관리 능력', 'sub_category': '시간관리능력', 'competency_name': '시간관리능력', 'level': 3},
            {'code': 'RES002', 'main_category': '자원관리 능력', 'sub_category': '예산관리능력', 'competency_name': '예산관리능력', 'level': 3},
            {'code': 'RES003', 'main_category': '자원관리 능력', 'sub_category': '물적자원관리능력', 'competency_name': '물적자원관리능력', 'level': 3},
            {'code': 'RES004', 'main_category': '자원관리 능력', 'sub_category': '인적자원관리능력', 'competency_name': '인적자원관리능력', 'level': 3},

            # 문제해결 능력
            {'code': 'PRO001', 'main_category': '문제해결 능력', 'sub_category': '사고력', 'competency_name': '사고력', 'level': 3},
            {'code': 'PRO002', 'main_category': '문제해결 능력', 'sub_category': '문제처리능력', 'competency_name': '문제처리능력', 'level': 3},

            # 정보능력
            {'code': 'INF001', 'main_category': '정보능력', 'sub_category': '컴퓨터 활용능력', 'competency_name': '컴퓨터 활용능력', 'level': 3},
            {'code': 'INF002', 'main_category': '정보능력', 'sub_category': '정보처리능력', 'competency_name': '정보처리능력', 'level': 3},

            # 조직이해 능력
            {'code': 'ORG001', 'main_category': '조직이해 능력', 'sub_category': '국제감각', 'competency_name': '국제감각', 'level': 3},
            {'code': 'ORG002', 'main_category': '조직이해 능력', 'sub_category': '조직 체제 이해능력', 'competency_name': '조직 체제 이해능력', 'level': 3},
            {'code': 'ORG003', 'main_category': '조직이해 능력', 'sub_category': '경영이해능력', 'competency_name': '경영이해능력', 'level': 3},
            {'code': 'ORG004', 'main_category': '조직이해 능력', 'sub_category': '업무이해능력', 'competency_name': '업무이해능력', 'level': 3},

            # 수리능력
            {'code': 'MAT001', 'main_category': '수리능력', 'sub_category': '기초연산능력', 'competency_name': '기초연산능력', 'level': 3},
            {'code': 'MAT002', 'main_category': '수리능력', 'sub_category': '기초통계능력', 'competency_name': '기초통계능력', 'level': 3},
            {'code': 'MAT003', 'main_category': '수리능력', 'sub_category': '도표분석능력', 'competency_name': '도표분석능력', 'level': 3},
            {'code': 'MAT004', 'main_category': '수리능력', 'sub_category': '도표작성능력', 'competency_name': '도표작성능력', 'level': 3},

            # 자기개발 능력
            {'code': 'SEL001', 'main_category': '자기개발 능력', 'sub_category': '자아인식능력', 'competency_name': '자아인식능력', 'level': 3},
            {'code': 'SEL002', 'main_category': '자기개발 능력', 'sub_category': '자기관리능력', 'competency_name': '자기관리능력', 'level': 3},
            {'code': 'SEL003', 'main_category': '자기개발 능력', 'sub_category': '경력개발능력', 'competency_name': '경력개발능력', 'level': 3},

            # 대인관계 능력
            {'code': 'INT001', 'main_category': '대인관계 능력', 'sub_category': '팀웍능력', 'competency_name': '팀웍능력', 'level': 3},
            {'code': 'INT002', 'main_category': '대인관계 능력', 'sub_category': '리더십능력', 'competency_name': '리더십능력', 'level': 3},
            {'code': 'INT003', 'main_category': '대인관계 능력', 'sub_category': '갈등관리능력', 'competency_name': '갈등관리능력', 'level': 3},
            {'code': 'INT004', 'main_category': '대인관계 능력', 'sub_category': '협상능력', 'competency_name': '협상능력', 'level': 3},
            {'code': 'INT005', 'main_category': '대인관계 능력', 'sub_category': '고객서비스능력', 'competency_name': '고객서비스능력', 'level': 3},

            # 기술능력
            {'code': 'TEC001', 'main_category': '기술능력', 'sub_category': '기술이해능력', 'competency_name': '기술이해능력', 'level': 3},
            {'code': 'TEC002', 'main_category': '기술능력', 'sub_category': '기술선택능력', 'competency_name': '기술선택능력', 'level': 3},
            {'code': 'TEC003', 'main_category': '기술능력', 'sub_category': '기술적용능력', 'competency_name': '기술적용능력', 'level': 3},
            
            # 직업윤리
            {'code': 'ETH001', 'main_category': '직업윤리', 'sub_category': '근로윤리', 'competency_name': '근로윤리', 'level': 3},
            {'code': 'ETH002', 'main_category': '직업윤리', 'sub_category': '공동체윤리', 'competency_name': '공동체윤리', 'level': 3},
        ]
        
        created_count = 0
        for comp_data in competencies:
            obj, created = NCSCompetency.objects.get_or_create(
                code=comp_data['code'],
                defaults=comp_data
            )
            if created:
                created_count += 1
                self.stdout.write(f"Created: {obj.competency_name}")
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} competencies'))