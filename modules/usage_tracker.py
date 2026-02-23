"""
OCR 사용량 추적 모듈

월별 Cloud Vision API 호출 횟수를 파일로 관리합니다.
"""

import json
import os
from datetime import datetime

USAGE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".ocr_usage.json")
MONTHLY_LIMIT = 950  # 무료 한도 1,000건 중 여유분 50건 확보


def _load_usage() -> dict:
    """사용량 파일을 읽습니다."""
    if not os.path.exists(USAGE_FILE):
        return {}
    with open(USAGE_FILE, "r") as f:
        return json.load(f)


def _save_usage(data: dict):
    """사용량 파일에 저장합니다."""
    with open(USAGE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_current_month_key() -> str:
    """현재 월 키 (예: '2026-02')"""
    return datetime.now().strftime("%Y-%m")


def get_monthly_count() -> int:
    """이번 달 사용 횟수를 반환합니다."""
    data = _load_usage()
    key = get_current_month_key()
    return data.get(key, 0)


def increment_count():
    """사용 횟수를 1 증가시킵니다."""
    data = _load_usage()
    key = get_current_month_key()
    data[key] = data.get(key, 0) + 1
    _save_usage(data)


def is_within_limit() -> bool:
    """무료 한도 내인지 확인합니다."""
    return get_monthly_count() < MONTHLY_LIMIT


def get_remaining() -> int:
    """남은 무료 횟수를 반환합니다."""
    return max(0, MONTHLY_LIMIT - get_monthly_count())
