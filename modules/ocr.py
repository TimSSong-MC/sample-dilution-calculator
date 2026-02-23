"""
OCR 모듈 - Google Cloud Vision (고품질) + EasyOCR (무료 폴백)

사용자가 OCR 엔진을 선택할 수 있습니다.
"""

import re
import streamlit as st


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
    numbers = re.findall(r"\d+\.?\d*", full_text)
    float_numbers = [float(n) for n in numbers if 0 < float(n) < 10000]
    return float_numbers, full_text


# ─── Google Cloud Vision ─────────────────────────────
def _extract_with_cloud_vision(image_bytes: bytes) -> tuple[list[float], str]:
    """Google Cloud Vision API로 숫자 추출."""
    from google.cloud import vision
    from google.oauth2 import service_account

    # Streamlit Secrets에서 인증
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
    numbers = re.findall(r"\d+\.?\d*", full_text)
    float_numbers = [float(n) for n in numbers if 0 < float(n) < 10000]
    return float_numbers, full_text


# ─── 통합 인터페이스 ─────────────────────────────────
def extract_numbers_from_image(
    image_bytes: bytes,
    engine: str = "easyocr",
) -> list[float]:
    """
    선택된 엔진으로 이미지에서 숫자를 추출합니다.

    Args:
        image_bytes: 이미지 바이트 데이터
        engine: "cloud_vision" 또는 "easyocr"

    Returns:
        추출된 숫자 리스트
    """
    try:
        if engine == "cloud_vision":
            numbers, raw_text = _extract_with_cloud_vision(image_bytes)
        else:
            numbers, raw_text = _extract_with_easyocr(image_bytes)

        if raw_text:
            st.info(f"📝 인식된 원문:\n```\n{raw_text}\n```")

        if not numbers:
            st.warning("이미지에서 숫자를 인식하지 못했습니다.")

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
