from django.contrib.auth.models import User
from accounts.models import School, Teacher, Class, Student
from cp.models import ContentType

# 1. 학교 생성
school = School.objects.create(
    name="진전중학교",
    address="경상남도 창원시 마산합포구 진전면 진전중학교로"
)

# 2. 컨텐츠 타입 생성
content_types = [
    {"type_name": "선택형", "description": "객관식 문제"},
    {"type_name": "단답형", "description": "단답형 문제"},
    {"type_name": "서술형", "description": "서술형 문제"},
    {"type_name": "빈칸채우기", "description": "빈칸을 채우는 문제"},
    {"type_name": "순서정하기", "description": "순서를 맞추는 문제"},
]

for ct_data in content_types:
    ContentType.objects.get_or_create(**ct_data)

# 3. 교사 계정 생성
teacher_user = User.objects.create_user(
    username='tc0001',
    password='muhan5337',
    first_name='Daewook',
    last_name='Jeong',
    email='teacher@test.com'
)

teacher = Teacher.objects.create(
    user=teacher_user,
    school=school,
    employee_id='T001',
    phone='010-1234-5678'
)

# 4. 학급 생성
class_2_1 = Class.objects.create(
    school=school,
    teacher=teacher,
    grade=2,
    class_number=1,
    name='2학년 1반'
)

# 5. 학생 계정 생성
student_user = User.objects.create_user(
    username='25010101',
    password='010101',
    first_name='철수',
    last_name='김',
    email='student@test.com'
)

student = Student.objects.create(
    user=student_user,
    school_class=class_2_1,
    student_id='25010101',
    birth_date='2010-01-01'
)

print("초기 데이터 설정 완료!")