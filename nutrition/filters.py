import django_filters

from nutrition.models import Allergen, StudentAllergy, SchoolMeal, SchoolMealItem


class AllergenFilter(django_filters.FilterSet):
    class Meta:
        model = Allergen
        fields = ("code", "name")


class StudentAllergyFilter(django_filters.FilterSet):
    class Meta:
        model = StudentAllergy
        fields = ("student", "allergen")


class SchoolMealFilter(django_filters.FilterSet):
    meal_date_gte = django_filters.DateFilter(field_name="meal_date", lookup_expr="gte")
    meal_date_lte = django_filters.DateFilter(field_name="meal_date", lookup_expr="lte")
    source_updated_at_gte = django_filters.DateFilter(
        field_name="source_updated_at", lookup_expr="gte"
    )
    source_updated_at_lte = django_filters.DateFilter(
        field_name="source_updated_at", lookup_expr="lte"
    )
    fetched_at_gte = django_filters.DateTimeFilter(
        field_name="fetched_at", lookup_expr="gte"
    )
    fetched_at_lte = django_filters.DateTimeFilter(
        field_name="fetched_at", lookup_expr="lte"
    )

    class Meta:
        model = SchoolMeal
        fields = ("school", "meal_date", "meal_type", "source_updated_at", "fetched_at")


class SchoolMealItemFilter(django_filters.FilterSet):
    class Meta:
        model = SchoolMealItem
        fields = ("meal", "name", "allergens")
