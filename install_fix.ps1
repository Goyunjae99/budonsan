# 네이버 부동산 크롤러 설치 스크립트 (오류 수정 버전)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "네이버 부동산 크롤러 설치 스크립트" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Python 버전 확인
Write-Host "[0/5] Python 버전 확인 중..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host "  $pythonVersion" -ForegroundColor White
Write-Host ""

Write-Host "[1/5] pip 업그레이드 중..." -ForegroundColor Yellow
python -m pip install --upgrade pip
Write-Host ""

Write-Host "[2/5] wheel 및 setuptools 업그레이드 중..." -ForegroundColor Yellow
python -m pip install --upgrade wheel setuptools
Write-Host ""

Write-Host "[3/5] greenlet 설치 시도 (사전 빌드된 wheel 사용)..." -ForegroundColor Yellow
python -m pip install --only-binary :all: greenlet
if ($LASTEXITCODE -ne 0) {
    Write-Host "  사전 빌드된 wheel이 없습니다. 소스에서 빌드 시도..." -ForegroundColor Yellow
    python -m pip install greenlet --no-build-isolation
}
Write-Host ""

Write-Host "[4/5] 나머지 패키지 설치 중..." -ForegroundColor Yellow
Write-Host "  - playwright 설치 중..." -ForegroundColor Gray
python -m pip install playwright
if ($LASTEXITCODE -ne 0) {
    Write-Host "  playwright 설치 실패. 재시도 중..." -ForegroundColor Yellow
    python -m pip install playwright --no-cache-dir
}

Write-Host "  - PySide6 설치 중..." -ForegroundColor Gray
python -m pip install PySide6

Write-Host "  - pandas 설치 중..." -ForegroundColor Gray
python -m pip install pandas

Write-Host "  - openpyxl 설치 중..." -ForegroundColor Gray
python -m pip install openpyxl
Write-Host ""

Write-Host "[5/5] Playwright 브라우저 설치 중..." -ForegroundColor Yellow
python -m playwright install chromium
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "경고: Playwright 브라우저 설치에 실패했습니다." -ForegroundColor Yellow
    Write-Host "프로그램 실행 시 자동으로 설치를 시도합니다." -ForegroundColor Yellow
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "설치가 완료되었습니다!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "설치 확인 중..." -ForegroundColor Yellow
python -c "import playwright; print('✓ playwright 설치됨')" 2>$null
python -c "import PySide6; print('✓ PySide6 설치됨')" 2>$null
python -c "import pandas; print('✓ pandas 설치됨')" 2>$null
python -c "import openpyxl; print('✓ openpyxl 설치됨')" 2>$null
Write-Host ""
Write-Host "프로그램 실행: python main.py" -ForegroundColor Cyan
Write-Host ""
pause
