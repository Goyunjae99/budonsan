# 대안 설치 방법: 개별 패키지 설치

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "대안 설치 방법: 개별 패키지 설치" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "이 스크립트는 requirements.txt를 사용하지 않고" -ForegroundColor Yellow
Write-Host "각 패키지를 개별적으로 설치합니다." -ForegroundColor Yellow
Write-Host ""

# pip 업그레이드
Write-Host "[1/7] pip 업그레이드..." -ForegroundColor Yellow
python -m pip install --upgrade pip
Write-Host ""

# wheel, setuptools
Write-Host "[2/7] wheel, setuptools 설치..." -ForegroundColor Yellow
python -m pip install --upgrade wheel setuptools
Write-Host ""

# greenlet (여러 방법 시도)
Write-Host "[3/7] greenlet 설치 시도..." -ForegroundColor Yellow
Write-Host "  방법 1: 사전 빌드된 wheel 사용..." -ForegroundColor Gray
python -m pip install --only-binary :all: greenlet 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  방법 2: 최신 버전 설치..." -ForegroundColor Gray
    python -m pip install greenlet>=3.0.0 --no-build-isolation 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  방법 3: 특정 버전 설치..." -ForegroundColor Gray
        python -m pip install greenlet==3.1.1 2>$null
    }
}
Write-Host ""

# playwright
Write-Host "[4/7] playwright 설치..." -ForegroundColor Yellow
python -m pip install playwright --no-cache-dir
Write-Host ""

# PySide6
Write-Host "[5/7] PySide6 설치..." -ForegroundColor Yellow
python -m pip install PySide6 --no-cache-dir
Write-Host ""

# pandas
Write-Host "[6/7] pandas 설치..." -ForegroundColor Yellow
python -m pip install pandas --no-cache-dir
Write-Host ""

# openpyxl
Write-Host "[7/7] openpyxl 설치..." -ForegroundColor Yellow
python -m pip install openpyxl --no-cache-dir
Write-Host ""

# 브라우저 설치
Write-Host "Playwright 브라우저 설치 중..." -ForegroundColor Yellow
python -m playwright install chromium
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "설치 완료!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
pause
