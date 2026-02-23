"""
🧪 DNA/RNA 시료 희석 계산기 (Sample Dilution Calculator)

시료 사진 업로드 → OCR 농도 추출 → 편집 → 자동 계산
"""

import streamlit as st
import pandas as pd
from modules.calculator import calculate_dilution, format_result_text
from modules.ocr import extract_numbers_from_image, is_cloud_vision_configured
from modules.usage_tracker import get_monthly_count, get_remaining, is_within_limit, increment_count, MONTHLY_LIMIT

# ─── 페이지 설정 ─────────────────────────────────────
st.set_page_config(
    page_title="🧬 DNA Input양 계산기",
    page_icon="🧬",
    layout="centered",
)

# ─── 커스텀 CSS ──────────────────────────────────────
st.markdown("""
<style>
    /* ─── 기본 스타일 ─── */
    .main-title {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #1c7ed6, #20c997);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        color: #868e96;
        font-size: 1rem;
        margin-bottom: 2rem;
    }

    /* ─── 모바일 최적화 (필수) ─── */
    /* 입력 필드 확대 방지 (iOS Safari) */
    input, select, textarea {
        font-size: 16px !important;
    }
    
    /* 데이터 테이블/에디터 가로 스크롤 */
    .stDataFrame, .stDataEditor {
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
    }

    /* ─── 공통 컴포넌트 디자인 (Soft Tint) ─── */
    /* 버튼 스타일 통일 */
    .stButton > button {
        border-radius: 12px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease-in-out !important;
    }
    /* Primary 버튼 (계산하기 등) */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #339af0, #20c997) !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(32, 201, 151, 0.2) !important;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(32, 201, 151, 0.3) !important;
    }

    /* 설정 영역 (회색 박스) 배경 부여 */
    [data-testid="stHorizontalBlock"] {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 16px;
        border: 1px solid #f1f3f5;
    }

    /* 라디오 버튼 (프리셋/입력방식 등) 카드형 디자인 (공통) */
    .stRadio > div[role="radiogroup"] {
        gap: 12px !important;
    }
    .stRadio > div[role="radiogroup"] > label {
        padding: 12px 20px !important;
        background-color: #ffffff;
        border: 1px solid #e9ecef !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02) !important;
        transition: all 0.2s ease !important;
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 0 !important;
    }
    .stRadio > div[role="radiogroup"] > label:hover {
        background-color: #e7f5ff !important;
        border-color: #74c0fc !important;
    }

    /* 메트릭 카드 간격 */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        color: #343a40;
    }
    [data-testid="stMetricLabel"] {
        font-weight: 600;
        color: #868e96;
    }

    /* 모바일 반응형 */
    @media (max-width: 768px) {
        .main-title {
            font-size: 1.5rem;
        }
        .subtitle {
            font-size: 0.85rem;
            margin-bottom: 1rem;
        }

        /* Streamlit 기본 패딩 축소 */
        .block-container {
            padding: 1.5rem 1rem !important;
        }

        /* 사이드바 기본 숨김 */
        [data-testid="stSidebar"] {
            min-width: 0px;
        }

        /* 라디오 버튼 세로 배치 (계단식 수정) */
        .stRadio > div[role="radiogroup"] {
            flex-direction: column !important;
            align-items: stretch !important; /* 계단식(너비 불일치) 해결! */
            gap: 10px !important;
        }
        .stRadio > div[role="radiogroup"] > label {
            width: 100% !important; /* 세로형 꽉 차게 */
            padding: 14px !important;
        }

        /* 메트릭 카드 축소 */
        [data-testid="stMetricValue"] {
            font-size: 1.2rem;
        }

        /* 파일 업로더 터치 영역 */
        [data-testid="stFileUploader"] {
            min-height: 100px;
        }
        [data-testid="stFileUploader"] section {
            padding: 20px !important;
        }

        /* 코드 블록 스크롤 */
        .stCode {
            max-height: 300px;
            overflow-y: auto;
        }
    }

    /* 작은 모바일 (< 480px) */
    @media (max-width: 480px) {
        .main-title {
            font-size: 1.3rem;
        }
        .block-container {
            padding: 0.5rem 0.5rem !important;
        }
    }
</style>

<!-- 모바일 뷰포트 확대 방지 -->
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
#  로그인 인증
# ═══════════════════════════════════════════════════════
def check_login():
    """secrets.toml의 [auth] 섹션에서 사용자 인증을 확인합니다."""
    # 인증 설정이 없으면 로그인 없이 통과
    try:
        auth = st.secrets["auth"]
    except (KeyError, FileNotFoundError):
        return True

    if st.session_state.get("authenticated"):
        return True

    st.markdown('<p class="main-title">🧬 DNA Input양 계산기</p>', unsafe_allow_html=True)
    st.markdown("---")
    st.subheader("🔐 로그인")

    with st.form("login_form"):
        username = st.text_input("아이디", placeholder="아이디를 입력하세요")
        password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
        submitted = st.form_submit_button("로그인", use_container_width=True, type="primary")

        if submitted:
            # secrets.toml의 [auth] 섹션에서 사용자 확인
            valid_users = dict(auth)
            if username in valid_users and valid_users[username] == password:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("❌ 아이디 또는 비밀번호가 틀렸습니다.")

    return False


# 로그인 체크
if not check_login():
    st.stop()

# ─── 로그인 성공 후 메인 앱 ────────────────────────────
# 로그아웃 버튼 (사이드바)
with st.sidebar:
    if st.session_state.get("username"):
        st.write(f"👤 **{st.session_state.username}** 님")
    if st.button("🚪 로그아웃"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.rerun()


# ─── 타이틀 ──────────────────────────────────────────
st.markdown('<p class="main-title">🧬 DNA Input양 계산기</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">'
    '사진 업로드 → OCR 농도 추출 → 목표 질량에 맞는 Input·Low TE 혼합량 자동 계산'
    '</p>',
    unsafe_allow_html=True,
)

# ─── 1. 설정 ─────────────────────────────────────
st.subheader("⚙️ 설정")

# 프리셋
PRESETS = {
    "1000ng / 50μL (기본)": (1000.0, 50.0),
    "2700ng / 300μL": (2700.0, 300.0),
    "직접 입력": None,
}
preset = st.radio("프리셋 선택", list(PRESETS.keys()), horizontal=True)

if PRESETS[preset] is not None:
    target_mass, target_volume = PRESETS[preset]
else:
    col1, col2 = st.columns(2)
    with col1:
        target_mass = st.number_input(
            "목표 질량 (ng)",
            value=1000.0,
            min_value=1.0,
            step=100.0,
        )
    with col2:
        target_volume = st.number_input(
            "최종 볼륨 (μL)",
            value=50.0,
            min_value=1.0,
            step=10.0,
        )

st.caption(f"🎯 목표: **{target_mass:.0f}ng** / **{target_volume:.0f}μL**")
st.divider()

# ─── 2. 데이터 입력 (OCR 또는 수동) ──────────────────
st.subheader("📋 농도 데이터 입력")

input_mode = st.radio(
    "입력 방식 선택",
    ["📸 이미지 OCR", "✏️ 수동 입력"],
    horizontal=True,
)

# 세션 상태 초기화
if "conc_data" not in st.session_state:
    st.session_state.conc_data = pd.DataFrame({
        "순번": range(1, 9),
        "농도 (ng/μL)": [0.0] * 8,
    })

if input_mode == "📸 이미지 OCR":
    # OCR 엔진 선택
    cloud_vision_ready = is_cloud_vision_configured()
    engine_options = ["EasyOCR (무료, 로컬)"]
    if cloud_vision_ready:
        engine_options.insert(0, "Cloud Vision (고품질, 추천)")

    selected_engine = st.selectbox(
        "OCR 엔진 선택",
        engine_options,
        help="Cloud Vision은 손글씨 인식률이 월등히 높습니다",
    )
    engine_key = "cloud_vision" if "Cloud Vision" in selected_engine else "easyocr"

    # Cloud Vision 사용량 표시
    if engine_key == "cloud_vision":
        remaining = get_remaining()
        used = get_monthly_count()
        st.caption(f"📊 이번 달 Cloud Vision 사용: **{used}건** / {MONTHLY_LIMIT}건 (잔여: {remaining}건)")
        if not is_within_limit():
            st.error(f"❌ 이번 달 무료 한도({MONTHLY_LIMIT}건)를 초과했습니다. EasyOCR을 사용해주세요.")

    # 파일 업로더 강조 CSS
    st.markdown("""
    <style>
        [data-testid="stFileUploader"] {
            border: 3px dashed #1c7ed6 !important;
            border-radius: 12px !important;
            padding: 20px !important;
            background-color: #e7f5ff !important;
            transition: all 0.2s;
        }
        [data-testid="stFileUploader"]:hover {
            background-color: #d0ebff !important;
            border-color: #1971c2 !important;
        }
        [data-testid="stFileUploader"] section {
            padding: 10px !important;
        }
    </style>
    """, unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "📷 농도 데이터 사진을 여기에 업로드하세요",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        help="여러 장을 한 번에 업로드할 수 있습니다",
    )

    if uploaded_files:
        st.caption(f"📎 **{len(uploaded_files)}장** 업로드됨")

        # 이미지 프리뷰 + 순서 지정
        file_order = []
        cols = st.columns(min(len(uploaded_files), 3))
        for idx, f in enumerate(uploaded_files):
            with cols[idx % 3]:
                st.image(f, caption=f.name, width=150)
                order = st.number_input(
                    f"순서",
                    min_value=1,
                    max_value=len(uploaded_files),
                    value=idx + 1,
                    key=f"order_{idx}",
                )
                file_order.append((order, idx, f))

        # 순서대로 정렬
        file_order.sort(key=lambda x: x[0])

        can_run = True
        if engine_key == "cloud_vision":
            needed = len(uploaded_files)
            if get_remaining() < needed:
                st.error(
                    f"❌ Cloud Vision 잔여 {get_remaining()}건인데 "
                    f"{needed}장을 처리해야 합니다. EasyOCR을 사용하거나 이미지를 줄여주세요."
                )
                can_run = False

        if can_run and st.button("🔍 OCR 실행", type="primary"):
            all_numbers = []
            progress = st.progress(0, text="OCR 처리 중...")

            for i, (order, orig_idx, f) in enumerate(file_order):
                progress.progress(
                    (i + 1) / len(file_order),
                    text=f"({i+1}/{len(file_order)}) {f.name} 처리 중...",
                )
                image_bytes = f.getvalue()
                if engine_key == "cloud_vision":
                    increment_count()
                numbers = extract_numbers_from_image(image_bytes, engine=engine_key)
                if numbers:
                    st.caption(f"📄 **{f.name}**: {len(numbers)}개 숫자 인식")
                    all_numbers.extend(numbers)

            progress.empty()

            if all_numbers:
                st.session_state.conc_data = pd.DataFrame({
                    "순번": range(1, len(all_numbers) + 1),
                    "농도 (ng/μL)": all_numbers,
                })
                st.success(
                    f"✅ 총 {len(all_numbers)}개의 숫자를 인식했습니다 "
                    f"({len(file_order)}장). 아래에서 검수해주세요."
                )
            else:
                    st.error("숫자를 인식하지 못했습니다. 수동 입력을 이용해주세요.")

else:
    # 수동 입력 모드 - 샘플 수 설정
    sample_count = st.number_input(
        "전체 샘플 수",
        min_value=1,
        max_value=96,
        value=8,
        step=8,
        help="8, 16, 24 단위로 입력하세요",
    )
    if st.button("🔄 행 수 적용"):
        st.session_state.conc_data = pd.DataFrame({
            "순번": range(1, sample_count + 1),
            "농도 (ng/μL)": [0.0] * sample_count,
        })
        st.rerun()

# 편집 가능 테이블
st.caption("💡 아래 표에서 농도를 직접 수정하거나, 행을 추가/삭제할 수 있습니다.")
edited_df = st.data_editor(
    st.session_state.conc_data,
    num_rows="dynamic",
    column_config={
        "순번": st.column_config.NumberColumn("순번", disabled=True),
        "농도 (ng/μL)": st.column_config.NumberColumn(
            "농도 (ng/μL)",
            min_value=0.0,
            format="%.1f",
            help="Puri. 후 측정된 농도",
        ),
    },
    use_container_width=True,
    key="conc_editor",
)

st.divider()

# ─── 3. 계산 실행 ────────────────────────────────────
if st.button("🧮 계산하기", type="primary", use_container_width=True):
    concentrations = edited_df["농도 (ng/μL)"].tolist()

    if not concentrations or all(c == 0 for c in concentrations):
        st.error("❌ 농도 데이터를 입력해주세요.")
    else:
        result_df = calculate_dilution(concentrations, target_mass, target_volume)
        result_df["농도 (ng/μL)"] = result_df["농도 (ng/μL)"].round(1)

        # ─── 4. 결과 표시 ────────────────────────────
        st.subheader("📊 계산 결과")

        # 요약 통계
        ok_count = len(result_df[result_df["상태"].str.contains("✅")])
        warn_count = len(result_df[result_df["상태"].str.contains("⚠️")])
        err_count = len(result_df[result_df["상태"].str.contains("❌")])

        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("✅ 정상", f"{ok_count}개")
        mc2.metric("⚠️ 농도 부족", f"{warn_count}개")
        mc3.metric("❌ 에러", f"{err_count}개")

        # 결과 테이블 (스타일링)
        def style_result_table(df):
            """Input 컬럼 노란 강조 + 8행 단위 배경 + 부족 행 표시"""
            styles = pd.DataFrame("", index=df.index, columns=df.columns)

            for idx in df.index:
                row_num = idx  # 0-based index
                # 8행 단위 배경 (0-7: 흰색, 8-15: 연파랑, ...)
                if (row_num // 8) % 2 == 1:
                    styles.loc[idx, :] = "background-color: #d0ebff;"

                # Input 컬럼 노란 강조
                if df.loc[idx, "Input (μL)"] != "-":
                    styles.loc[idx, "Input (μL)"] = "background-color: #fff3bf; font-weight: 600;"

                # 농도 부족 행
                if "⚠️" in str(df.loc[idx, "상태"]):
                    styles.loc[idx, "상태"] = "color: #e67700; font-weight: 600;"
                elif "❌" in str(df.loc[idx, "상태"]):
                    styles.loc[idx, "상태"] = "color: #e03131; font-weight: 600;"

            return styles

        styled_df = result_df.style.apply(
            lambda _: style_result_table(result_df), axis=None
        ).format({
            "농도 (ng/μL)": "{:.1f}",
            "최종 볼륨 (μL)": "{}",
        })
        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
        )

        # 경고 시료 안내
        if warn_count > 0:
            st.warning(
                f"⚠️ {warn_count}개 시료는 농도가 부족하여 "
                f"{target_volume:.0f}μL 안에 {target_mass:.0f}ng을 담을 수 없습니다.\n\n"
                "최종 볼륨을 늘리거나 시료를 농축해야 합니다."
            )

        # 복사용 텍스트
        st.divider()
        result_text = format_result_text(result_df, target_mass, target_volume)
        st.code(result_text, language=None)
        st.caption("👆 위 텍스트를 선택하여 복사하세요")

# ─── 푸터 ────────────────────────────────────────────
st.divider()
st.caption(
    "🧬 DNA Input양 계산기 v1.0 | "
    "목표 질량과 최종 볼륨을 자유롭게 설정하세요"
)
