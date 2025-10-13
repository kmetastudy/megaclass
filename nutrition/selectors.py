import uuid
from typing import Optional

from django.db.models import QuerySet

from common.utils import get_object
from nutrition.models import Allergen, StudentAllergy, SchoolMeal, SchoolMealItem
from nutrition.filters import (
    AllergenFilter,
    StudentAllergyFilter,
    SchoolMealFilter,
    SchoolMealItemFilter,
)


def allergen_list(*, filters=None) -> QuerySet[Allergen]:
    filters = filters or {}

    qs = Allergen.objects.all()

    return AllergenFilter(filters, qs).qs


def allergen_get(*, allergen_id: uuid.UUID) -> Optional[Allergen]:
    return get_object(Allergen, id=allergen_id)


def student_allergy_list(*, filters=None) -> QuerySet[StudentAllergy]:
    filters = filters or {}

    qs = StudentAllergy.objects.select_related("student", "allergen").all()

    return StudentAllergyFilter(filters, qs).qs


def student_allergy_get(*, student_allergy_id: uuid.UUID) -> Optional[StudentAllergy]:
    return get_object(
        StudentAllergy.objects.select_related("student", "allergen"),
        id=student_allergy_id,
    )


def school_meal_list(*, filters=None) -> QuerySet[SchoolMeal]:
    filters = filters or {}

    qs = SchoolMeal.objects.select_related("school").all()

    return SchoolMealFilter(filters, qs).qs


def school_meal_get(*, meal_id: uuid.UUID) -> Optional[SchoolMeal]:
    return get_object(SchoolMeal.objects.select_related("school"), id=meal_id)


def school_meal_item_list(*, filters=None) -> QuerySet[SchoolMealItem]:
    filters = filters or {}

    qs = (
        SchoolMealItem.objects.select_related("meal")
        .prefetch_related("allergens")
        .all()
    )

    return SchoolMealItemFilter(filters, qs).qs


def school_meal_item_get(*, item_id: uuid.UUID) -> Optional[SchoolMealItem]:
    return get_object(
        SchoolMealItem.objects.select_related("meal").prefetch_related("allergens"),
        id=item_id,
    )
