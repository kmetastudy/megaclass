import uuid
from datetime import date
from typing import Optional

from django.db import transaction

from common.services import model_update
from nutrition.models import Allergen, StudentAllergy, SchoolMeal, SchoolMealItem
from nutrition.utils import (
    parse_calories,
    parse_date,
    map_meal_type_code,
    parse_dish_items,
)
from accounts.models import Student, School


# =============================================================================
# Allergen Services
# =============================================================================


@transaction.atomic
def allergen_create(*, code: int, name: str, description: str = "") -> Allergen:
    allergen = Allergen(code=code, name=name, description=description)

    allergen.full_clean()
    allergen.save()

    return allergen


@transaction.atomic
def allergen_update(*, allergen: Allergen, data: dict) -> Allergen:
    fields = ["code", "name", "description"]

    allergen, has_updated = model_update(instance=allergen, fields=fields, data=data)

    return allergen


@transaction.atomic
def allergen_delete(*, allergen: Allergen) -> None:
    allergen.delete()


# =============================================================================
# StudentAllergy Services
# =============================================================================


@transaction.atomic
def student_allergy_create(
    *, student: Student, allergen: Allergen, notes: str = ""
) -> StudentAllergy:
    student_allergy = StudentAllergy(student=student, allergen=allergen, notes=notes)

    student_allergy.full_clean()
    student_allergy.save()

    return student_allergy


@transaction.atomic
def student_allergy_update(
    *, student_allergy: StudentAllergy, data: dict
) -> StudentAllergy:
    fields = ["notes"]

    student_allergy, has_updated = model_update(
        instance=student_allergy, fields=fields, data=data
    )

    return student_allergy


@transaction.atomic
def student_allergy_delete(*, student_allergy: StudentAllergy) -> None:
    student_allergy.delete()


# =============================================================================
# SchoolMeal Services
# =============================================================================


@transaction.atomic
def school_meal_create(
    *,
    school: School,
    meal_date: date,
    meal_type: str,
    calories: float,
    raw_meal_name: str,
    origin_information: str = "",
    nutrition_information: str = "",
    served_count: Optional[int] = None,
    source_updated_at: Optional[date] = None,
) -> SchoolMeal:
    school_meal = SchoolMeal(
        school=school,
        meal_date=meal_date,
        meal_type=meal_type,
        calories=calories,
        raw_meal_name=raw_meal_name,
        origin_information=origin_information,
        nutrition_information=nutrition_information,
        served_count=served_count,
        source_updated_at=source_updated_at,
    )

    school_meal.full_clean()
    school_meal.save()

    return school_meal


@transaction.atomic
def school_meal_update(*, school_meal: SchoolMeal, data: dict) -> SchoolMeal:
    fields = [
        "meal_date",
        "meal_type",
        "calories",
        "raw_meal_name",
        "origin_information",
        "nutrition_information",
        "served_count",
        "source_updated_at",
    ]

    school_meal, has_updated = model_update(
        instance=school_meal, fields=fields, data=data
    )

    return school_meal


@transaction.atomic
def school_meal_delete(*, school_meal: SchoolMeal) -> None:
    school_meal.delete()


# =============================================================================
# SchoolMealItem Services
# =============================================================================


@transaction.atomic
def school_meal_item_create(
    *,
    meal: SchoolMeal,
    name: str,
    allergen_codes: Optional[list[int]] = None,
    description: str = "",
) -> SchoolMealItem:
    school_meal_item = SchoolMealItem(meal=meal, name=name, description=description)

    school_meal_item.full_clean()
    school_meal_item.save()

    # 알레르기 요소 매핑
    if allergen_codes:
        allergens = Allergen.objects.filter(code__in=allergen_codes)
        school_meal_item.allergens.set(allergens)

    return school_meal_item


@transaction.atomic
def school_meal_item_update(
    *, school_meal_item: SchoolMealItem, data: dict
) -> SchoolMealItem:
    fields = ["name", "description", "allergens"]

    school_meal_item, has_updated = model_update(
        instance=school_meal_item, fields=fields, data=data
    )

    return school_meal_item


@transaction.atomic
def school_meal_item_delete(*, school_meal_item: SchoolMealItem) -> None:
    school_meal_item.delete()


# =============================================================================
# NEIS API Integration Service
# =============================================================================


@transaction.atomic
def school_meal_create_from_api_data(*, school: School, api_data: dict) -> SchoolMeal:
    """
    NEIS OpenAPI 응답 데이터로부터 SchoolMeal과 SchoolMealItem들을 생성

    Args:
        school: 학교 객체
        api_data: NEIS API 응답 데이터 (단일 급식 정보)

    Returns:
        생성된 SchoolMeal 객체

    Example API data:
        {
            "MMEAL_SC_CODE": "3",
            "MLSV_YMD": "20251009",
            "CAL_INFO": "1048.2 Kcal",
            "DDISH_NM": "친환경찰보리밥 <br/>얼갈이된장국 (5.6)<br/>...",
            "ORPLC_INFO": "...",
            "NTR_INFO": "...",
            "MLSV_FGR": 90.0,
            "LOAD_DTM": "20251001"
        }
    """
    # 1. API 데이터 파싱
    meal_date = parse_date(api_data["MLSV_YMD"])
    meal_type = map_meal_type_code(api_data["MMEAL_SC_CODE"])
    calories = parse_calories(api_data["CAL_INFO"])
    raw_meal_name = api_data["DDISH_NM"]
    origin_information = api_data.get("ORPLC_INFO", "")
    nutrition_information = api_data.get("NTR_INFO", "")
    served_count = api_data.get("MLSV_FGR")
    source_updated_at = (
        parse_date(api_data["LOAD_DTM"]) if api_data.get("LOAD_DTM") else None
    )

    # 2. SchoolMeal 생성
    school_meal = school_meal_create(
        school=school,
        meal_date=meal_date,
        meal_type=meal_type,
        calories=calories,
        raw_meal_name=raw_meal_name,
        origin_information=origin_information,
        nutrition_information=nutrition_information,
        served_count=int(served_count) if served_count else None,
        source_updated_at=source_updated_at,
    )

    # 3. DDISH_NM 파싱하여 메뉴 항목들 추출
    dish_items = parse_dish_items(raw_meal_name)

    # 4. 각 메뉴 항목에 대해 SchoolMealItem 생성
    for item in dish_items:
        school_meal_item_create(
            meal=school_meal,
            name=item["name"],
            allergen_codes=item["allergen_codes"],
        )

    return school_meal
