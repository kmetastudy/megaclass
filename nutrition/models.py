import uuid

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from common.models import BaseModel
from accounts.models import Student, School

# Create your models here.


class Allergen(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.IntegerField(
        unique=True, validators=[MinValueValidator(1), MaxValueValidator(19)]
    )
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["code"]
        verbose_name = "알레르기 유발 식품"
        verbose_name_plural = "알레르기 유발 식품"

    def __str__(self):
        return self.name


class StudentAllergy(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="학생")
    allergen = models.ForeignKey(
        Allergen, on_delete=models.CASCADE, verbose_name="알레르기 요소"
    )
    notes = models.TextField(blank=True, verbose_name="비고")

    class Meta:
        unique_together = ["student", "allergen"]
        verbose_name = "학생 알레르기 정보"
        verbose_name_plural = "학생 알레르기 기록"

    def __str__(self):
        return f"{self.student} - {self.allergen.name}"


class SchoolMeal(BaseModel):
    class MealType(models.TextChoices):
        BREAKFAST = "breakfast", "조식"
        LUNCH = "lunch", "중식"
        DINNER = "dinner", "석식"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(School, on_delete=models.CASCADE, verbose_name="학교")
    meal_date = models.DateField(verbose_name="급식 날짜")
    meal_type = models.CharField(
        max_length=20,
        choices=MealType.choices,
        default=MealType.LUNCH,
        verbose_name="식사 구분",
    )
    calories = models.FloatField(
        validators=[MinValueValidator(0)], verbose_name="칼로리 (kcal)"
    )
    raw_meal_name = models.TextField(verbose_name="요리명 원본")
    origin_information = models.TextField(blank=True, verbose_name="원산지 정보")
    nutrition_information = models.TextField(blank=True, verbose_name="영양 정보")

    served_count = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="급식 인원수"
    )

    # 원본 데이터가 마지막으로 수정된 시각 (neis openapi에서의 수정 일자)
    source_updated_at = models.DateField(
        null=True, blank=True, verbose_name="원본 데이터 최종 수정 일자"
    )

    # neis openapi에서 정보를 가져온 시각
    fetched_at = models.DateTimeField(
        auto_now_add=True, verbose_name="정보 가져온 시각"
    )

    class Meta:
        unique_together = ["school", "meal_date", "meal_type"]
        # ordering = ["-date"]
        verbose_name = "학교 급식 정보"
        verbose_name_plural = "학교 급식 정보"

    def __str__(self):
        return f"{self.school.name} - {self.meal_date} - {self.get_meal_type_display()}"


class SchoolMealItem(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meal = models.ForeignKey(SchoolMeal, on_delete=models.CASCADE, verbose_name="급식")
    name = models.CharField(max_length=100, verbose_name="식단명")
    allergens = models.ManyToManyField(
        Allergen, blank=True, verbose_name="알레르기 유발 식품"
    )
    description = models.TextField(blank=True, verbose_name="설명")

    class Meta:
        verbose_name = "학교 급식 항목"
        verbose_name_plural = "학교 급식 항목"

    def __str__(self):
        return f"{self.meal} - {self.name}"
