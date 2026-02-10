# 설치 가이드

## 시스템 요구사항

- Python 3.8 이상 (3.11 또는 3.12 권장)
- Windows 10 이상
- 인터넷 연결

## 설치 방법

### 자동 설치 (권장)

#### PowerShell 사용
```powershell
.\install.ps1
```

#### CMD 사용
```cmd
install.bat
```

### 수동 설치

#### 1단계: pip 업그레이드
```bash
python -m pip install --upgrade pip wheel setuptools
```

#### 2단계: 패키지 설치
```bash
python -m pip install -r requirements.txt
```

#### 3단계: Playwright 브라우저 설치
```bash
python -m playwright install chromium
```

## 설치 오류 해결

### 오류 1: greenlet 빌드 오류

**증상:**
```
error: failed building wheel for greenlet
fatal error C1189: #error: "this header requires PY_BUILD_CORE define"
```

**해결 방법:**

1. **사전 빌드된 wheel 사용:**
```bash
python -m pip install --only-binary :all: greenlet
python -m pip install -r requirements.txt
```

2. **Python 버전 확인:**
   - Python 3.14는 일부 패키지와 호환성 문제가 있을 수 있습니다.
   - Python 3.11 또는 3.12 사용을 권장합니다.

3. **Visual C++ 빌드 도구 설치:**
   - [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) 설치
   - 또는 [Visual Studio Community](https://visualstudio.microsoft.com/) 설치

### 오류 2: playwright 명령어 인식 불가

**증상:**
```
playwright: 'playwright' 용어가 cmdlet, 함수, 스크립트 파일 또는 실행할 수 있는 프로그램 이름으로 인식되지 않습니다.
```

**해결 방법:**

`playwright` 명령어 대신 Python 모듈로 실행:
```bash
python -m playwright install chromium
```

### 오류 3: 패키지 설치 실패

**해결 방법:**

1. **개별 패키지 설치:**
```bash
python -m pip install playwright
python -m pip install PySide6
python -m pip install pandas
python -m pip install openpyxl
python -m pip install greenlet
```

2. **캐시 클리어 후 재설치:**
```bash
python -m pip cache purge
python -m pip install -r requirements.txt --no-cache-dir
```

3. **가상 환경 사용:**
```bash
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
```

## 설치 확인

설치가 완료되었는지 확인:

```bash
python -c "import playwright; import PySide6; import pandas; import openpyxl; print('모든 패키지가 정상적으로 설치되었습니다!')"
```

## 프로그램 실행

설치 완료 후:

```bash
python main.py
```

## 추가 도움말

문제가 계속되면 다음을 확인하세요:

1. Python 버전: `python --version`
2. pip 버전: `python -m pip --version`
3. 인터넷 연결 상태
4. 방화벽/보안 소프트웨어 설정
