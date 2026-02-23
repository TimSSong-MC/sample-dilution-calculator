"""
DNA Input양 계산 모듈

공식:
    Input(μL) = ceil(목표 질량(ng) ÷ 현재 농도(ng/μL))  ← 올림 정수
    Low TE(μL) = 최종 볼륨(μL) - Input(μL)
"""

import math
import pandas as pd


def calculate_dilution(
    concentrations: list[float],
    target_mass_ng: float = 1000.0,
    target_volume_ul: float = 50.0,
) -> pd.DataFrame:
    """
    농도 리스트로부터 Input량과 Low TE량을 계산합니다.
    Input은 소수점 첫째자리에서 올림하여 정수로 표시합니다.
    """
    results = []

    for i, conc in enumerate(concentrations, 1):
        if conc is None or conc <= 0:
            results.append({
                "순번": i,
                "농도 (ng/μL)": conc if conc is not None else 0,
                "Input (μL)": "-",
                "Low TE (μL)": "-",
                "최종 볼륨 (μL)": int(target_volume_ul),
                "상태": "❌ 농도 0 이하",
            })
            continue

        # 올림 정수 처리
        sample_vol = math.ceil(target_mass_ng / conc)

        if sample_vol > target_volume_ul:
            max_mass = conc * target_volume_ul
            results.append({
                "순번": i,
                "농도 (ng/μL)": conc,
                "Input (μL)": int(target_volume_ul),
                "Low TE (μL)": 0,
                "최종 볼륨 (μL)": int(target_volume_ul),
                "상태": f"⚠️ 농도 부족 (최대 {max_mass:.0f}ng)",
            })
        else:
            water_vol = int(target_volume_ul) - sample_vol
            results.append({
                "순번": i,
                "농도 (ng/μL)": conc,
                "Input (μL)": sample_vol,
                "Low TE (μL)": water_vol,
                "최종 볼륨 (μL)": int(target_volume_ul),
                "상태": "✅ 정상",
            })

    return pd.DataFrame(results)


def format_result_text(
    df: pd.DataFrame,
    target_mass_ng: float,
    target_volume_ul: float,
) -> str:
    """결과를 복사용 텍스트로 포맷합니다."""
    lines = [f"[목표: {target_mass_ng:.0f}ng / {target_volume_ul:.0f}μL]", ""]

    for _, row in df.iterrows():
        conc = row["농도 (ng/μL)"]
        sample = row["Input (μL)"]
        lte = row["Low TE (μL)"]

        if "농도 부족" in str(row["상태"]):
            lines.append(
                f"{row['순번']}. {conc} ng/μL: 농도 부족 ({target_volume_ul:.0f}μL 초과)"
            )
        elif "농도 0" in str(row["상태"]):
            lines.append(f"{row['순번']}. 계산 불가")
        else:
            lines.append(
                f"{row['순번']}. {conc} ng/μL: "
                f"Input {sample}μL + Low TE {lte}μL"
            )

    return "\n".join(lines)
