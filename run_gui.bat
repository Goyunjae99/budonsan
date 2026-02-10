@echo off
chcp 65001 >nul
setlocal

REM 실행 위치를 스크립트 위치로 고정
pushd "%~dp0"

echo ========================================
echo 네이버 부동산 매물 크롤러 자동 설치 & 실행
echo ========================================
echo.

echo [1/3] pip 업그레이드 중...
python -m pip install --upgrade pip >nul 2>&1
echo 완료
echo.

echo [2/3] 패키지 설치 중...
python -m pip install --upgrade wheel setuptools >nul 2>&1
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [오류] 패키지 설치에 실패했습니다.
    echo install_fix.ps1 또는 QUICK_FIX.md를 참고해주세요.
    echo.
    pause
    popd
    exit /b 1
)
echo.

echo [3/3] Playwright 브라우저 설치 중...
python -m playwright install chromium
if errorlevel 1 (
    echo.
    echo [경고] Playwright 브라우저 설치 실패. 계속 진행합니다.
    echo.
)

echo.
echo 프로그램 실행 중...
python main.py
if errorlevel 1 (
    echo.
    echo [오류] 프로그램 실행에 실패했습니다.
    echo 파이썬/패키지 설치 상태를 확인해주세요.
    echo.
    pause
    popd
    exit /b 1
)

popd
endlocal
