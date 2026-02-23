"""
OCR 사용량 추적 모듈

월별 Cloud Vision API 호출 횟수를 Supabase(클라우드 DB)에 기록합니다.
(배포 환경에서 서버가 재부팅되어도 사용량이 유지됩니다.)
만약 Supabase 설정이 없다면 로컬 파일(.ocr_usage.json)에 저장하는 폴백으로 동작합니다.
"""

import json
import os
import requests
from datetime import datetime
import streamlit as st

USAGE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".ocr_usage.json")
MONTHLY_LIMIT = 950  # 무료 한도 1,000건 중 여유분 50건 확보

def _get_supabase_config():
    """Supabase 설정 정보를 반환합니다."""
    try:
        if "supabase" in st.secrets:
            return st.secrets["supabase"]["SUPABASE_URL"], st.secrets["supabase"]["SUPABASE_KEY"]
    except Exception:
        pass
    return None, None

def _get_headers(api_key: str) -> dict:
    return {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

def get_current_month_key() -> str:
    """현재 월 키 (예: '2026-02')"""
    return datetime.now().strftime("%Y-%m")

def get_monthly_count() -> int:
    """이번 달 사용 횟수를 Supabase 또는 로컬 파일에서 읽어옵니다."""
    url, key = _get_supabase_config()
    month_key = get_current_month_key()
    
    # 1. Supabase 사용
    if url and key:
        table_url = f"{url}/rest/v1/ocr_usage?month_key=eq.{month_key}&select=usage_count"
        try:
            response = requests.get(table_url, headers=_get_headers(key), timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    return data[0].get("usage_count", 0)
                else:
                    return 0
        except Exception as e:
            print(f"Supabase 조회 에러 (로컬 읽기로 대체): {e}")

    # 2. 로컬 파일 폴백
    if not os.path.exists(USAGE_FILE):
        return 0
    try:
        with open(USAGE_FILE, "r") as f:
            data = json.load(f)
            return data.get(month_key, 0)
    except Exception:
        return 0

def increment_count(amount: int = 1):
    """사용 횟수를 증가시키고 Supabase 또는 로컬 파일에 저장합니다."""
    url, key = _get_supabase_config()
    month_key = get_current_month_key()
    current_count = get_monthly_count()
    new_count = current_count + amount

    # 1. Supabase 사용
    if url and key:
        table_url = f"{url}/rest/v1/ocr_usage"
        headers = _get_headers(key)
        
        try:
            if current_count == 0:
                # 레코드가 없으면 POST로 새 행 생성
                payload = {"month_key": month_key, "usage_count": new_count}
                response = requests.post(table_url, headers=headers, json=payload, timeout=5)
            else:
                # 이미 있으면 PATCH로 업데이트
                patch_url = f"{table_url}?month_key=eq.{month_key}"
                payload = {"usage_count": new_count}
                response = requests.patch(patch_url, headers=headers, json=payload, timeout=5)
            
            if response.status_code in [200, 201, 204]:
                return  # 성공 시 여기서 종료
            else:
                print(f"Supabase 기록 실패: {response.status_code} {response.text}")
        except Exception as e:
            print(f"Supabase 업데이트 에러 (로컬 저장으로 대체): {e}")

    # 2. 로컬 파일 폴백
    local_data = {}
    if os.path.exists(USAGE_FILE):
        try:
            with open(USAGE_FILE, "r") as f:
                local_data = json.load(f)
        except Exception:
            pass
    
    local_data[month_key] = new_count
    try:
        with open(USAGE_FILE, "w") as f:
            json.dump(local_data, f, indent=2)
    except Exception:
        pass


def is_within_limit() -> bool:
    """무료 한도 내인지 확인합니다."""
    return get_monthly_count() < MONTHLY_LIMIT


def get_remaining() -> int:
    """남은 무료 횟수를 반환합니다."""
    return max(0, MONTHLY_LIMIT - get_monthly_count())
