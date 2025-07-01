# student/utils.py
import json
from django.utils import timezone
from django.db import connection
from .models import StudentAnswer
from accounts.models import Student
from teacher.models import ChasiSlide


def parse_correct_answer(answer_text):
    """Contents의 answer 필드에서 실제 정답을 추출하는 함수"""
    if not answer_text:
        return ''
    
    answer_text = answer_text.strip()
    
    # JSON 형태인지 확인
    if answer_text.startswith('{') and answer_text.endswith('}'):
        try:
            # JSON 파싱 시도
            answer_data = json.loads(answer_text)
            # 'answer' 키의 값을 문자열로 반환
            correct_answer = str(answer_data.get('answer', ''))
            print(f"JSON에서 파싱된 정답: '{correct_answer}'")
            return correct_answer
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 실패: {e}")
            # JSON 파싱 실패시 원본 텍스트 반환
            return answer_text
    else:
        # 일반 텍스트
        return answer_text


def update_existing_answer(existing_answer, student_answer, correct_answer, is_correct):
    """기존 답안을 업데이트하는 함수"""
    try:
        answer_data = {
            'selected_answer': student_answer,
            'correct_answer': correct_answer,
            'answer_type': 'resubmit',
            'submitted_at': timezone.now().isoformat()
        }
        
        existing_answer.answer = answer_data
        existing_answer.is_correct = is_correct
        existing_answer.score = 100.0 if is_correct else 0.0
        existing_answer.submitted_at = timezone.now()
        existing_answer.feedback = '자동 채점 결과 (재제출)'
        existing_answer.save()
        
        print(f"기존 답안 업데이트 완료: {existing_answer.id}")
        return existing_answer
        
    except Exception as e:
        print(f"기존 답안 업데이트 실패: {e}")
        return None


def create_new_answer(student, slide, student_answer, correct_answer, is_correct):
    """
    새 답안을 생성하는 함수 - Django ORM만 사용하여 안전하게 생성
    """
    try:
        print("=== 새 답안 생성(ORM) 시작 ===")
        from django.utils import timezone

        answer_data = {
            'selected_answer': student_answer,
            'correct_answer': correct_answer,
            'answer_type': 'first_submit',
            'submitted_at': timezone.now().isoformat()
        }

        # **핵심 수정** : 다른 Raw SQL / FK 비활성화 로직 전부 제거하고 ORM만 사용
        student_answer_obj = StudentAnswer.objects.create(
            student=student,
            slide=slide,
            answer=answer_data,
            is_correct=is_correct,
            score=100.0 if is_correct else 0.0,
            feedback='자동 채점 결과'
        )

        print(f"ORM으로 생성 성공: {student_answer_obj.id}")
        return student_answer_obj

    except Exception as e:
        print(f"새 답안 생성 실패(ORM): {e}")
        import traceback
        print(traceback.format_exc())
        return None

def create_new_answer_0606(student, slide, student_answer, correct_answer, is_correct):
    """새 답안을 생성하는 함수 - 간단한 우회 방법"""
    try:
        print(f"=== 새 답안 생성 시작 ===")
        print(f"Student ID: {student.id}, ChasiSlide ID: {slide.id}")
        
        # 1단계: 외래키 존재 확인
        student_exists = Student.objects.filter(id=student.id).exists()
        slide_exists = ChasiSlide.objects.filter(id=slide.id).exists()
        
        print(f"Student 존재: {student_exists}, ChasiSlide 존재: {slide_exists}")
        
        if not student_exists or not slide_exists:
            print("ERROR: 외래키 객체가 존재하지 않음")
            return None
        
        # 2단계: 가장 간단한 방법으로 생성
        answer_data = {
            'selected_answer': student_answer,
            'correct_answer': correct_answer,
            'answer_type': 'first_submit',
            'submitted_at': timezone.now().isoformat()
        }
        
        try:
            # 방법 1: 외래키 제약조건 임시 비활성화 (SQLite)
            print("외래키 제약조건 임시 비활성화 시도...")
            return create_with_fk_disabled(student, slide, answer_data, is_correct)
        except Exception as e:
            print(f"외래키 비활성화 방법 실패: {e}")
            
        try:
            # 방법 2: 최소한의 필드만 사용
            print("최소 필드 방법 시도...")
            return create_with_minimal_fields(student.id, slide.id, answer_data, is_correct)
        except Exception as e:
            print(f"최소 필드 방법 실패: {e}")
            
        try:
            # 방법 3: 일반 ORM (마지막 시도)
            print("일반 ORM 방법 시도...")
            return create_answer_with_orm(student, slide, answer_data, is_correct)
        except Exception as e:
            print(f"일반 ORM 방법 실패: {e}")
            
        print("모든 방법 실패")
        return None
        
    except Exception as e:
        print(f"새 답안 생성 전체 실패: {e}")
        import traceback
        print(f"트레이스백: {traceback.format_exc()}")
        return None


def create_with_fk_disabled(student, slide, answer_data, is_correct):
    """외래키 제약조건을 임시로 비활성화하고 생성"""
    from django.db import transaction
    
    with connection.cursor() as cursor:
        # SQLite 외래키 제약조건 비활성화
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        try:
            with transaction.atomic():
                student_answer_obj = StudentAnswer.objects.create(
                    student_id=student.id,
                    slide_id=slide.id,
                    answer=answer_data,
                    is_correct=is_correct,
                    score=100.0 if is_correct else 0.0,
                    feedback='자동 채점 결과'
                )
                print(f"외래키 비활성화로 생성 성공: {student_answer_obj.id}")
                return student_answer_obj
        finally:
            # 외래키 제약조건 다시 활성화
            cursor.execute("PRAGMA foreign_keys = ON")


def create_with_minimal_fields(student_id, slide_id, answer_data, is_correct):
    """최소한의 필드만 사용해서 생성"""
    import json
    
    with connection.cursor() as cursor:
        # 가장 기본적인 INSERT
        cursor.execute("""
            INSERT INTO student_studentanswer 
            (student_id, slide_id, answer, is_correct, score, feedback, submitted_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """, [
            student_id,
            slide_id,
            json.dumps(answer_data),
            is_correct,
            100.0 if is_correct else 0.0,
            '자동 채점 결과'
        ])
        
        # 생성된 ID 가져오기
        cursor.execute("SELECT last_insert_rowid()")
        answer_id = cursor.fetchone()[0]
        
        print(f"최소 필드로 생성 성공: {answer_id}")
        
        # ORM 객체로 반환
        return StudentAnswer.objects.get(id=answer_id)


def check_student_exists(student_id):
    """Student가 실제로 존재하는지 확인"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM student_student WHERE id = ?", [student_id])
            count = cursor.fetchone()[0]
            return count > 0
    except Exception as e:
        print(f"Student 존재 확인 실패: {e}")
        return False


def check_slide_exists(slide_id):
    """ChasiSlide가 실제로 존재하는지 확인"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM teacher_chasislide WHERE id = ?", [slide_id])
            count = cursor.fetchone()[0]
            return count > 0
    except Exception as e:
        print(f"ChasiSlide 존재 확인 실패: {e}")
        return False


def check_student_relations(student):
    """Student의 관련 객체들이 모두 존재하는지 확인"""
    try:
        print(f"Student 관계 확인:")
        print(f"  - User ID: {student.user.id if student.user else 'None'}")
        print(f"  - School Class ID: {student.school_class.id if student.school_class else 'None'}")
        
        # User 존재 확인
        if student.user:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM auth_user WHERE id = ?", [student.user.id])
                user_exists = cursor.fetchone()[0] > 0
                print(f"  - User 존재: {user_exists}")
        
        # Class 존재 확인 (테이블 이름은 실제에 맞게 수정 필요)
        if student.school_class:
            try:
                with connection.cursor() as cursor:
                    # 실제 Class 테이블 이름으로 수정 필요
                    cursor.execute("SELECT COUNT(*) FROM student_class WHERE id = ?", [student.school_class.id])
                    class_exists = cursor.fetchone()[0] > 0
                    print(f"  - Class 존재: {class_exists}")
            except Exception as e:
                print(f"  - Class 확인 실패: {e}")
        
    except Exception as e:
        print(f"Student 관계 확인 실패: {e}")


def create_answer_with_raw_sql(student_id, slide_id, answer_data, is_correct):
    """Raw SQL로 StudentAnswer 생성 시도"""
    try:
        import json
        from django.utils import timezone
        
        score = 100.0 if is_correct else 0.0
        now = timezone.now()
        
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO student_studentanswer 
                (student_id, slide_id, answer, submitted_at, is_correct, score, feedback)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [
                student_id,
                slide_id, 
                json.dumps(answer_data),
                now,
                is_correct,
                score,
                '자동 채점 결과'
            ])
            
            # 생성된 ID 가져오기
            cursor.execute("SELECT last_insert_rowid()")
            answer_id = cursor.fetchone()[0]
            
            print(f"Raw SQL로 생성 성공: {answer_id}")
            
            # ORM 객체로 반환
            return StudentAnswer.objects.get(id=answer_id)
            
    except Exception as e:
        print(f"Raw SQL 생성 실패: {e}")
        return None


def create_answer_with_orm(student, slide, answer_data, is_correct):
    """일반 ORM으로 StudentAnswer 생성 시도"""
    try:
        student_answer_obj = StudentAnswer.objects.create(
            student=student,
            slide=slide,
            answer=answer_data,
            is_correct=is_correct,
            score=100.0 if is_correct else 0.0,
            feedback='자동 채점 결과'
        )
        
        print(f"ORM으로 생성 성공: {student_answer_obj.id}")
        return student_answer_obj
        
    except Exception as e:
        print(f"ORM 생성 실패: {e}")
        return None


def debug_foreign_keys():
    """외래키 제약조건을 확인하는 함수"""
    try:
        with connection.cursor() as cursor:
            # SQLite 외래키 설정 확인
            cursor.execute("PRAGMA foreign_keys;")
            fk_status = cursor.fetchone()[0]
            print(f"Foreign Keys 활성화: {fk_status}")
            
            # StudentAnswer 테이블 외래키 확인
            cursor.execute("PRAGMA foreign_key_list(student_studentanswer);")
            fk_list = cursor.fetchall()
            print("StudentAnswer 외래키 목록:")
            for fk in fk_list:
                print(f"  {fk}")
                
            # 테이블 구조 확인
            cursor.execute("PRAGMA table_info(student_studentanswer);")
            table_info = cursor.fetchall()
            print("StudentAnswer 테이블 구조:")
            for column in table_info:
                print(f"  {column}")
                
    except Exception as e:
        print(f"외래키 디버깅 실패: {e}")


def fix_student_class_issue(student):
    """Student의 school_class 문제를 해결하는 함수"""
    try:
        if not student.school_class:
            print("Student에 school_class가 없음 - 기본값 설정 시도")
            
            # 기본 클래스 찾기 또는 생성
            from .models import Class  # 실제 Class 모델 import
            
            default_class = Class.objects.first()
            if not default_class:
                # 기본 클래스 생성
                default_class = Class.objects.create(
                    grade=1,
                    class_number=1,
                    school_name='기본학교',
                    # 다른 필수 필드들...
                )
                print(f"기본 클래스 생성: {default_class}")
            
            student.school_class = default_class
            student.save()
            print(f"Student school_class 수정 완료: {default_class}")
            
    except Exception as e:
        print(f"Student school_class 수정 실패: {e}")