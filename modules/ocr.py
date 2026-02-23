"""
OCR 모듈 - Google Cloud Vision (고품질) + EasyOCR (무료 폴백)

농도(ng/μL) 값만 정확히 추출하는 스마트 파싱 로직 포함.
"""

import re
import streamlit as st


# ─── 스마트 농도 파싱 ─────────────────────────────────
def _parse_concentrations(full_text: str) -> list[float]:
    """
    OCR 원문에서 농도(ng/μL) 값만 추출합니다.

    우선순위:
    1. 'X.XX ng/μL' 패턴 (가장 정확)
    2. 'X.XX ng' 패턴
    3. 소수점 포함 숫자 중 농도 범위(0.1~9999) 필터링 (폴백)
    """
    concentrations = []

    # 1단계: "숫자 ng/μL" 또는 "숫자 ng/uL" 또는 "숫자 ng/ul" 패턴
    pattern_ng_ul = re.findall(
        r"(\d+\.?\d*)\s*ng\s*/\s*[μuU][lL]",
        full_text,
        re.IGNORECASE,
    )
    if pattern_ng_ul:
        concentrations = [float(n) for n in pattern_ng_ul]
        return concentrations

    # 2단계: "숫자 ng" 패턴 (μL 없이)
    pattern_ng = re.findall(
        r"(\d+\.?\d*)\s*ng(?!\s*/)",
        full_text,
        re.IGNORECASE,
    )
    if pattern_ng:
        concentrations = [float(n) for n in pattern_ng if 0 < float(n) < 10000]
        return concentrations

    # 3단계: 폴백 - 소수점 포함 숫자만 (정수 시간값 등 제외)
    # 소수점이 있는 숫자를 우선 추출
    decimal_numbers = re.findall(r"\d+\.\d+", full_text)
    if decimal_numbers:
        concentrations = [float(n) for n in decimal_numbers if 0 < float(n) < 10000]
        return concentrations

    # 4단계: 최종 폴백 - 모든 숫자 (0.1~9999 범위)
    all_numbers = re.findall(r"\d+\.?\d*", full_text)
    concentrations = [float(n) for n in all_numbers if 0 < float(n) < 10000]
    return concentrations


# ─── EasyOCR ─────────────────────────────────────────
@st.cache_resource
def _get_easyocr_reader():
    """EasyOCR Reader를 캐싱하여 재사용합니다."""
    import easyocr
    return easyocr.Reader(["en"], gpu=False)


def _extract_with_easyocr(image_bytes: bytes) -> tuple[list[float], str]:
    """EasyOCR로 숫자 추출."""
    reader = _get_easyocr_reader()
    results = reader.readtext(image_bytes)
    if not results:
        return [], ""
    full_text = " ".join([text for (_, text, _) in results])
    return _parse_concentrations(full_text), full_text


# ─── Google Cloud Vision ─────────────────────────────
def _extract_with_cloud_vision(image_bytes: bytes) -> tuple[list[float], str]:
    """Google Cloud Vision API로 숫자 추출."""
    from google.cloud import vision
    from google.oauth2 import service_account

    gcp_info = st.secrets["gcp_service_account"]
    credentials = service_account.Credentials.from_service_account_info(
        dict(gcp_info)
    )
    client = vision.ImageAnnotatorClient(credentials=credentials)
    image = vision.Image(content=image_bytes)
    response = client.text_detection(image=image)

    if response.error.message:
        raise RuntimeError(f"API 오류: {response.error.message}")

    texts = response.text_annotations
    if not texts:
        return [], ""

    full_text = texts[0].description
    return _parse_concentrations(full_text), full_text


# ─── 통합 인터페이스 ─────────────────────────────────
def extract_numbers_from_image(
    image_bytes: bytes,
    engine: str = "easyocr",
) -> list[float]:
    """
    선택된 엔진으로 이미지에서 농도(ng/μL) 값을 추출합니다.

    파싱 우선순위:
    1. "XX.X ng/μL" 패턴 매칭 (가장 정확)
    2. "XX.X ng" 패턴 매칭
    3. 소수점 포함 숫자 추출 (시간 등 정수값 제외)
    4. 전체 숫자 폴백
    """
    try:
        if engine == "cloud_vision":
            numbers, raw_text = _extract_with_cloud_vision(image_bytes)
        else:
            numbers, raw_text = _extract_with_easyocr(image_bytes)

        if raw_text:
            st.info(f"📝 인식된 원문:\n```\n{raw_text}\n```")

        if not numbers:
            st.warning("이미지에서 농도 값을 인식하지 못했습니다.")

        return numbers

    except Exception as e:
        st.error(f"OCR 처리 중 오류가 발생했습니다: {str(e)}")
        return []


def is_cloud_vision_configured() -> bool:
    """Google Cloud Vision API가 설정되어 있는지 확인."""
    try:
        return "gcp_service_account" in st.secrets
    except (FileNotFoundError, AttributeError):
        return False
