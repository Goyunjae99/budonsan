@echo off
chcp 65001 >nul
echo ========================================
echo 네이버 부동산 크롤러 설치 스크립트
echo ========================================
echo.

echo [1/3] pip 업그레이드 중...
python -m pip install --upgrade pip
echo.

echo [2/3] 패키지 설치 중...
python -m pip install --upgrade wheel setuptools
python -m pip install -r requirements.txt
echo.

echo [3/3] Playwright 브라우저 설치 중...
python -m playwright install chromium
echo.

echo ========================================
echo 설치가 완료되었습니다!
echo ========================================
echo.
echo 프로그램 실행: python main.py
pause
