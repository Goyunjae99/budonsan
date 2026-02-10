# 네이버 부동산 매물 크롤러 GUI 프로그램

네이버 부동산에서 특정 단지의 매물 정보를 크롤링하고 GUI를 통해 조회 및 저장할 수 있는 프로그램입니다.

## 주요 기능

### GUI 프로그램 (권장)
- **PySide6 기반 사용자 친화적 인터페이스**
- 실시간 크롤링 진행 상황 표시
- 매물 정보 테이블 뷰 (정렬 기능 포함)
- 통계 정보 표시 (전체 매물 수, 동별 매물 수 등)
- 엑셀 파일(.xlsx) 및 CSV 파일 저장 기능
- 크롤링 시작/중지 제어

### 크롤링 기능
- Playwright를 사용한 웹 크롤링
- '저/중/고'로 표시된 매물의 상세 층수 정보 추출
- 매물별 동, 가격, 면적, 층수 정보 수집
- 네이버 차단 방지를 위한 랜덤 대기 시간

## 프로젝트 구조

```
budonsan/
├── main.py                 # GUI 프로그램 진입점
├── gui/
│   ├── main_window.py      # 메인 윈도우 GUI
│   └── crawler_thread.py   # 크롤링 스레드 클래스
├── crawler/
│   └── naver_crawler.py    # 크롤러 로직
├── utils/
│   ├── excel_exporter.py   # 엑셀 저장 기능
│   └── data_processor.py   # 데이터 처리 유틸리티
├── requirements.txt        # 필요한 패키지 목록
└── PRD.md                 # 프로젝트 요구사항 문서
```

## 설치 방법

### 방법 1: 자동 설치 스크립트 사용 (권장)

**오류가 발생하는 경우:**
```powershell
.\install_fix.ps1
```
또는
```powershell
.\install_alternative.ps1
```

**정상 설치:**
```powershell
.\install.ps1
```

**Windows CMD:**
```cmd
install.bat
```

**빠른 해결 가이드는 `QUICK_FIX.md` 파일을 참고하세요.**

### 방법 2: 수동 설치

1. pip 업그레이드:
```bash
python -m pip install --upgrade pip wheel setuptools
```

2. 필요한 패키지 설치:
```bash
python -m pip install -r requirements.txt
```

만약 `greenlet` 빌드 오류가 발생하는 경우:
```bash
python -m pip install --only-binary :all: greenlet
python -m pip install -r requirements.txt
```

3. Playwright 브라우저 설치:
```bash
python -m playwright install chromium
```

**참고:** `playwright install` 명령어가 인식되지 않으면 `python -m playwright install`을 사용하세요.

### 설치 문제 해결

- **greenlet 빌드 오류**: Python 3.14 사용 시 일부 패키지와 호환성 문제가 있을 수 있습니다. Python 3.11 또는 3.12 사용을 권장합니다.
- **playwright 명령어 인식 불가**: `python -m playwright install chromium` 형식으로 실행하세요.

## 사용 방법

### GUI 프로그램 실행 (권장)

```bash
python main.py
```

또는 실행 배치 파일 사용:
```cmd
run_gui.bat
```

1. 프로그램 실행 후 URL 입력 필드에 센트럴파크 단지 URL이 기본값으로 표시됩니다.
2. "크롤링 시작" 버튼을 클릭하여 크롤링을 시작합니다.
3. 진행 상황은 실시간으로 표시되며, 수집된 매물 정보는 테이블에 자동으로 추가됩니다.
4. 크롤링 완료 후 "엑셀 저장" 또는 "CSV 저장" 버튼을 클릭하여 파일로 저장할 수 있습니다.

## 주요 화면 구성

- **상단 영역**: 단지 정보 및 URL 입력, 크롤링 제어 버튼
- **진행 상황 영역**: 진행률 프로그레스 바, 상태 메시지, 로그 텍스트 영역
- **매물 정보 테이블**: 수집된 매물 정보를 테이블 형태로 표시 (정렬 가능)
- **하단 영역**: 통계 정보 및 저장 버튼

## 주의사항

- 네이버 부동산의 HTML 구조가 변경되면 선택자를 수정해야 할 수 있습니다.
- 크롤링 시 네이버의 이용약관을 준수해주세요.
- 과도한 요청은 IP 차단을 받을 수 있으므로 적절한 대기 시간을 유지하세요.
- 크롤링 중에는 브라우저가 표시되며, 네트워크 상태에 따라 시간이 소요될 수 있습니다.

## 기술 스택

- **Python**: 3.8 이상
- **PySide6**: GUI 프레임워크
- **Playwright**: 웹 크롤링 라이브러리
- **pandas**: 데이터 처리
- **openpyxl**: 엑셀 파일 생성/편집

## 라이선스

이 프로젝트는 교육 및 개인 사용 목적으로 제작되었습니다. 네이버 부동산의 이용약관을 준수하여 사용해주세요.
