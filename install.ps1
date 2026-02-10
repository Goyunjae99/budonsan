# 네이버 부동산 크롤러 설치 스크립트 (PowerShell)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "네이버 부동산 크롤러 설치 스크립트" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/4] pip 업그레이드 중..." -ForegroundColor Yellow
python -m pip install --upgrade pip
Write-Host ""

Write-Host "[2/4] wheel 및 setuptools 업그레이드 중..." -ForegroundColor Yellow
python -m pip install --upgrade wheel setuptools
Write-Host ""

Write-Host "[3/4] 패키지 설치 중..." -ForegroundColor Yellow
Write-Host "  greenlet 먼저 설치 시도..." -ForegroundColor Gray
python -m pip install --only-binary :all: greenlet 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  greenlet 사전 빌드 wheel 없음, 소스 빌드 시도..." -ForegroundColor Gray
    python -m pip install greenlet --no-build-isolation 2>$null
}

Write-Host "  나머지 패키지 설치 중..." -ForegroundColor Gray
python -m pip install playwright PySide6 pandas openpyxl --no-cache-dir
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "패키지 설치 중 오류가 발생했습니다." -ForegroundColor Red
    Write-Host "install_fix.ps1 또는 install_alternative.ps1 스크립트를 사용해보세요." -ForegroundColor Yellow
    Write-Host "또는 QUICK_FIX.md 파일을 참고하세요." -ForegroundColor Yellow
    pause
    exit 1
}
Write-Host ""

Write-Host "[4/4] Playwright 브라우저 설치 중..." -ForegroundColor Yellow
python -m playwright install chromium
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "설치가 완료되었습니다!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "프로그램 실행: python main.py" -ForegroundColor Cyan
Write-Host ""
pause
