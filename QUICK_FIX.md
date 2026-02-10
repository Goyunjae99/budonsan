# 빠른 오류 해결 가이드

## 현재 오류 상황

1. **greenlet 빌드 오류**: C++ 컴파일러 오류로 인한 빌드 실패
2. **playwright 모듈 없음**: greenlet 설치 실패로 인해 playwright도 설치되지 않음

## 해결 방법

### 방법 1: 수정된 설치 스크립트 사용 (권장)

```powershell
.\install_fix.ps1
```

이 스크립트는:
- greenlet을 사전 빌드된 wheel로 먼저 설치 시도
- 실패 시 대안 방법으로 재시도
- 각 패키지를 개별적으로 설치하여 오류 추적 용이

### 방법 2: 대안 설치 스크립트 사용

```powershell
.\install_alternative.ps1
```

이 스크립트는 requirements.txt를 사용하지 않고 각 패키지를 개별 설치합니다.

### 방법 3: 수동 설치 (단계별)

#### 1단계: greenlet 설치 (여러 방법 시도)

```powershell
# 방법 1: 사전 빌드된 wheel 사용
python -m pip install --only-binary :all: greenlet

# 방법 2: 최신 버전 (빌드 없이)
python -m pip install greenlet --no-build-isolation

# 방법 3: 특정 버전
python -m pip install greenlet==3.1.1
```

#### 2단계: playwright 설치

```powershell
python -m pip install playwright --no-cache-dir
```

#### 3단계: 나머지 패키지 설치

```powershell
python -m pip install PySide6 --no-cache-dir
python -m pip install pandas --no-cache-dir
python -m pip install openpyxl --no-cache-dir
```

#### 4단계: Playwright 브라우저 설치

```powershell
python -m playwright install chromium
```

### 방법 4: Python 버전 변경 (근본 해결)

Python 3.14는 일부 패키지와 호환성 문제가 있을 수 있습니다.

**권장: Python 3.11 또는 3.12 사용**

1. [Python 3.12 다운로드](https://www.python.org/downloads/)
2. 새 Python 버전 설치
3. 가상 환경 생성:
```powershell
python3.12 -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
```

### 방법 5: Visual C++ Build Tools 설치

greenlet 빌드에 필요한 컴파일러가 없을 수 있습니다.

1. [Microsoft C++ Build Tools 다운로드](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
2. 설치 시 "C++ 빌드 도구" 워크로드 선택
3. 설치 후 재부팅
4. 다시 설치 시도

## 설치 확인

설치가 완료되었는지 확인:

```powershell
python -c "import playwright; print('✓ playwright OK')"
python -c "import PySide6; print('✓ PySide6 OK')"
python -c "import pandas; print('✓ pandas OK')"
python -c "import openpyxl; print('✓ openpyxl OK')"
```

모든 패키지가 정상적으로 import되면 설치 성공입니다.

## 여전히 문제가 있다면

1. **캐시 클리어 후 재시도:**
```powershell
python -m pip cache purge
python -m pip install --no-cache-dir -r requirements.txt
```

2. **가상 환경 사용:**
```powershell
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

3. **Python 버전 확인:**
```powershell
python --version
```
Python 3.11 또는 3.12 사용 권장
