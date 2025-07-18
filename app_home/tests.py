from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from accounts.models import Student, School, Class
from teacher.models import Course, Chapter, SubChapter, Chasi, ChasiSlide
from student.models import StudentProgress
from app_home.models import HealthHabitTracker
import json


class HealthHabitSubmissionTest(TestCase):
    """건강습관 제출 기능 테스트"""
    
    def setUp(self):
        """테스트 데이터 설정"""
        # 학교, 학급 생성
        self.school = School.objects.create(name="테스트학교")
        self.school_class = Class.objects.create(
            school=self.school,
            grade=3,
            class_number=1
        )
        
        # 사용자 및 학생 생성
        self.user = User.objects.create_user(
            username="student1",
            password="testpass123"
        )
        self.student = Student.objects.create(
            user=self.user,
            student_id="test_student_001",
            school_class=self.school_class,
            birth_date="2010-01-01"
        )
        
        # 교사 생성
        self.teacher_user = User.objects.create_user(
            username="teacher1",
            password="testpass123"
        )
        from accounts.models import Teacher
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            employee_id="teacher_001",
            school=self.school
        )
        
        # 코스와 슬라이드 생성
        self.course = Course.objects.create(
            subject_name="테스트 코스",
            target="3학년",
            teacher=self.teacher
        )
        self.chapter = Chapter.objects.create(
            subject=self.course,
            chapter_title="테스트 단원",
            chapter_order=1
        )
        self.sub_chapter = SubChapter.objects.create(
            chapter=self.chapter,
            sub_chapter_title="테스트 소단원",
            sub_chapter_order=1
        )
        self.chasi = Chasi.objects.create(
            sub_chapter=self.sub_chapter,
            chasi_title="테스트 차시",
            chasi_order=1
        )
        self.slide = ChasiSlide.objects.create(
            chasi=self.chasi,
            slide_number=1,
            is_active=True
        )
        
        self.client = Client()
        self.client.login(username="student1", password="testpass123")
    
    def test_health_habit_submission_updates_student_progress(self):
        """건강습관 제출 시 StudentProgress가 업데이트되는지 테스트"""
        # 1. 건강습관 트래커 생성
        tracker = HealthHabitTracker.objects.create(
            student=self.student,
            slide=self.slide,
            promises={"1": "바른 자세로 생활하기"},
            final_reflection="테스트 최종 소감"
        )
        
        # 2. 제출 전 StudentProgress 상태 확인
        progress_before = StudentProgress.objects.filter(
            student=self.student,
            slide=self.slide,
            is_completed=True
        ).exists()
        self.assertFalse(progress_before, "제출 전에는 완료 상태가 아니어야 함")
        
        # 3. 최종 제출 요청
        response = self.client.post(
            reverse('health_habit:submit_final'),
            data=json.dumps({
                'tracker_id': tracker.id,
                'final_reflection': '테스트 최종 소감 수정'
            }),
            content_type='application/json'
        )
        
        # 4. 응답 확인
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # 5. StudentProgress가 업데이트되었는지 확인
        progress_after = StudentProgress.objects.get(
            student=self.student,
            slide=self.slide
        )
        self.assertTrue(progress_after.is_completed, "제출 후 완료 상태로 변경되어야 함")
        self.assertIsNotNone(progress_after.completed_at, "완료 시간이 설정되어야 함")
        
        # 6. 트래커 상태 확인
        tracker.refresh_from_db()
        self.assertTrue(tracker.is_submitted, "트래커가 제출 상태로 변경되어야 함")
        self.assertIsNotNone(tracker.submitted_at, "제출 시간이 설정되어야 함")
    
    def test_submitted_tracker_prevents_modifications(self):
        """제출된 트래커는 수정할 수 없어야 함"""
        # 1. 제출된 트래커 생성
        tracker = HealthHabitTracker.objects.create(
            student=self.student,
            slide=self.slide,
            promises={"1": "바른 자세로 생활하기"},
            is_submitted=True
        )
        
        # 2. 약속 수정 시도 (실패해야 함)
        response = self.client.post(
            reverse('health_habit:save_promises'),
            data=json.dumps({
                'slide_id': self.slide.id,
                'promises': {"1": "수정된 약속"}
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('제출 완료', response_data['error'])
        
        # 3. 소감 저장 시도 (실패해야 함)  
        response = self.client.post(
            reverse('health_habit:save_reflection'),
            data=json.dumps({
                'tracker_id': tracker.id,
                'promise_number': 1,
                'week': 1,
                'day': 1,
                'reflection_text': '테스트 소감',
                'reflection_date': '2024-01-01',
                'reflection_time': '10:00'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('제출 완료', response_data['error'])
    
    def test_student_view_shows_readonly_when_submitted(self):
        """제출된 경우 학생 페이지가 읽기 전용으로 표시되는지 테스트"""
        # 1. 제출된 트래커 생성
        HealthHabitTracker.objects.create(
            student=self.student,
            slide=self.slide,
            promises={"1": "바른 자세로 생활하기"},
            final_reflection="최종 소감",
            is_submitted=True
        )
        
        # 2. 학생 페이지 요청
        response = self.client.get(
            reverse('health_habit:student_view', args=[self.slide.id])
        )
        
        # 3. 응답 확인
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_submitted'])
        self.assertEqual(response.context['final_reflection'], "최종 소감")
        
        # 4. 페이지에 완료 메시지가 포함되어 있는지 확인
        self.assertContains(response, "제출 완료")
        self.assertContains(response, "읽기 전용")