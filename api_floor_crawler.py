import json
import re
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

COMPLEX_NO = "117804"
URL = f"https://new.land.naver.com/complexes/{COMPLEX_NO}?tab=article"

# HAR 저장 경로
HAR_PATH = Path("network.har")

def main():
    with sync_playwright() as p:
        # ✅ 실제 크롬 채널 사용(설치되어 있으면 더 자연스럽게 동작)
        #   안 되면 channel="chrome" 줄을 지우면 playwright chromium로 동작함
        context = p.chromium.launch_persistent_context(
            user_data_dir="pw_real_profile",   # 새 프로필 폴더(권장). 기존 크롬 프로필을 쓰려면 여기를 바꿔야 함.
            channel="chrome",
            headless=False,
            locale="ko-KR",
            viewport={"width": 1280, "height": 900},
            record_har_path=str(HAR_PATH),
            record_har_content="embed",
        )

        page = context.new_page()

        # ✅ automation 흔적 약화 (완전 해결책은 아니지만 도움 됨)
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)

        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        time.sleep(3)

        # 사람처럼 탭/필터를 몇 번 눌러 네트워크 호출을 유도
        # UI 텍스트는 화면에 따라 달라질 수 있어 실패해도 계속 진행
        for text in ["매물", "매매", "전세", "월세"]:
            try:
                page.get_by_text(text).first.click(timeout=3000)
                time.sleep(2)
            except Exception:
                pass

        # 스크롤도 한 번(목록 로딩 유도)
        try:
            page.mouse.wheel(0, 1200)
            time.sleep(2)
        except Exception:
            pass

        print(f"\nHAR saved -> {HAR_PATH.resolve()}")
        context.close()

if __name__ == "__main__":
    main()
