import re
from datetime import date, datetime
from typing import Optional


def parse_calories(cal_info: str) -> float:
    """
    칼로리 정보 문자열에서 숫자 추출

    예: "1048.2 Kcal" → 1048.2
    """
    match = re.search(r"(\d+\.?\d*)", cal_info)
    if match:
        return float(match.group(1))
    return 0.0


def parse_date(date_str: str) -> date:
    """
    NEIS API 날짜 형식을 date 객체로 변환

    예: "20251009" → date(2025, 10, 9)
    """
    return datetime.strptime(date_str, "%Y%m%d").date()


def map_meal_type_code(meal_code: str) -> str:
    """
    NEIS API 식사 구분 코드를 SchoolMeal.MealType enum 값으로 매핑

    예: "1" → "breakfast", "2" → "lunch", "3" → "dinner"
    """
    mapping = {
        "1": "breakfast",
        "2": "lunch",
        "3": "dinner",
    }
    return mapping.get(meal_code, "lunch")


def extract_allergen_codes(dish_name: str) -> list[int]:
    """
    메뉴명에서 알레르기 코드 추출

    예: "얼갈이된장국 (5.6)" → [5, 6]
    예: "친환경찰보리밥" → []
    """
    match = re.search(r"\(([0-9.]+)\)", dish_name)
    if match:
        codes_str = match.group(1)
        # 점으로 구분된 숫자들을 추출
        codes = [int(code) for code in codes_str.split(".") if code]
        return codes
    return []


def parse_dish_items(raw_dish_name: str) -> list[dict[str, any]]:
    """
    NEIS API DDISH_NM 필드를 파싱하여 개별 메뉴 항목과 알레르기 코드 추출

    예:
    "친환경찰보리밥 <br/>얼갈이된장국 (5.6)<br/>우엉어묵조림 (1.5.6.13.18)"
    →
    [
        {"name": "친환경찰보리밥", "allergen_codes": []},
        {"name": "얼갈이된장국", "allergen_codes": [5, 6]},
        {"name": "우엉어묵조림", "allergen_codes": [1, 5, 6, 13, 18]}
    ]
    """
    # <br/> 태그로 분리
    items = re.split(r"<br\s*/?>", raw_dish_name, flags=re.IGNORECASE)

    result = []
    for item in items:
        item = item.strip()
        if not item:
            continue

        # 알레르기 코드 추출
        allergen_codes = extract_allergen_codes(item)

        # 메뉴명에서 알레르기 코드 부분 제거
        name = re.sub(r"\s*\([0-9.]+\)\s*", "", item).strip()

        result.append(
            {
                "name": name,
                "allergen_codes": allergen_codes,
            }
        )

    return result
