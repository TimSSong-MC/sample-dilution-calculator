# 🧬 DNA Input양 계산기

사진 업로드 → OCR 농도 추출 → 목표 질량에 맞는 Input·Low TE 혼합량 자동 계산

## 🚀 기능

- **이미지 OCR**: 여러 장의 농도 데이터 사진 업로드 → 자동 숫자 추출
- **OCR 엔진 선택**: Cloud Vision (고품질) / EasyOCR (무료)
- **프리셋**: 1000ng/50μL, 2700ng/300μL 또는 직접 입력
- **Input 올림 처리**: 소수점 올림하여 정수 표시
- **시각적 결과**: Input 노란색 강조, 8행 단위 배경 구분
- **로그인 인증**: 팀원만 사용 가능
- **모바일 최적화**: 터치 친화적 UI

## 📋 사용법

1. 로그인 (아이디/비밀번호)
2. 프리셋 선택 또는 목표 질량·볼륨 직접 입력
3. 이미지 OCR 또는 수동으로 농도 입력
4. 🧮 계산하기 클릭
5. 결과 확인 및 복사

## 🔧 로컬 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

## ☁️ Streamlit Cloud 배포

1. 이 repo를 GitHub에 push
2. [share.streamlit.io](https://share.streamlit.io) 접속 → GitHub 연결
3. Main file: `app.py` → Deploy
4. Settings → Secrets에 아래 내용 추가:

```toml
[auth]
admin = "비밀번호"

[gcp_service_account]
# Google Cloud Vision API JSON 키 내용 (선택사항)
```

## 📁 프로젝트 구조

```
├── app.py                  # Streamlit 메인 앱
├── modules/
│   ├── calculator.py       # 희석 계산 로직 (올림 정수)
│   ├── ocr.py              # OCR (Cloud Vision + EasyOCR)
│   └── usage_tracker.py    # API 사용량 추적
├── requirements.txt
├── .streamlit/
│   ├── config.toml         # 테마 설정
│   └── secrets.toml.example # Secrets 템플릿
└── .gitignore
```
