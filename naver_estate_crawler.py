"""
네이버 부동산 매물 크롤링 스크립트
Playwright를 사용하여 네이버 부동산에서 매물 정보를 수집합니다.
"""

import asyncio
import csv
import random
import time
from datetime import datetime
from typing import List, Dict, Optional

from playwright.async_api import async_playwright, Page, Browser


class NaverEstateCrawler:
    """네이버 부동산 크롤러 클래스"""
    
    def __init__(self, url: str):
        self.url = url
        self.results: List[Dict[str, str]] = []
        
    async def wait_random(self, min_sec: float = 1.0, max_sec: float = 3.0):
        """랜덤 대기 시간 (네이버 차단 방지)"""
        wait_time = random.uniform(min_sec, max_sec)
        await asyncio.sleep(wait_time)
    
    async def extract_floor_info(self, page: Page, floor_text: str) -> str:
        """
        층수 정보 추출
        '저/중/고'로 표시된 경우 상세 페이지에서 정확한 층수 가져오기
        """
        # 이미 정확한 층수 형식인 경우 (예: "15/30층")
        if "/" in floor_text and "층" in floor_text:
            return floor_text.strip()
        
        # '저/중/고'로 표시된 경우 상세 페이지에서 가져오기
        if floor_text in ["저", "중", "고"]:
            try:
                # 상세 정보가 있는 요소 찾기
                # 네이버 부동산의 상세 페이지 구조에 맞게 선택자 수정 필요
                floor_detail = await page.query_selector("text=/\\d+\\/\\d+층/")
                if floor_detail:
                    floor_info = await floor_detail.inner_text()
                    return floor_info.strip()
                
                # 다른 선택자 시도
                floor_elements = await page.query_selector_all("[class*='floor'], [class*='층']")
                for element in floor_elements:
                    text = await element.inner_text()
                    if "/" in text and "층" in text:
                        return text.strip()
                        
            except Exception as e:
                print(f"층수 정보 추출 중 오류: {e}")
        
        return floor_text.strip()
    
    async def get_property_details(self, page: Page, property_element) -> Optional[Dict[str, str]]:
        """매물 상세 정보 가져오기"""
        try:
            # 매물 정보 추출
            property_info = {
                '동': '',
                '가격': '',
                '면적': '',
                '층수': ''
            }
            
            # 매물 텍스트 정보 가져오기
            property_text = await property_element.inner_text()
            
            # 동 정보 추출 (예: "101동", "1동" 등)
            dong_match = await property_element.query_selector("text=/\\d+동/")
            if dong_match:
                property_info['동'] = (await dong_match.inner_text()).strip()
            
            # 가격 정보 추출
            price_elements = await property_element.query_selector_all("[class*='price'], [class*='가격']")
            for elem in price_elements:
                price_text = await elem.inner_text()
                if "억" in price_text or "만원" in price_text or "원" in price_text:
                    property_info['가격'] = price_text.strip()
                    break
            
            # 면적 정보 추출
            area_elements = await property_element.query_selector_all("[class*='area'], [class*='면적'], [class*='㎡']")
            for elem in area_elements:
                area_text = await elem.inner_text()
                if "㎡" in area_text or "평" in area_text:
                    property_info['면적'] = area_text.strip()
                    break
            
            # 층수 정보 추출
            floor_elements = await property_element.query_selector_all("[class*='floor'], [class*='층']")
            floor_text = ""
            for elem in floor_elements:
                floor_text = await elem.inner_text()
                if floor_text:
                    break
            
            # 층수가 없으면 텍스트에서 직접 찾기
            if not floor_text:
                floor_match = await property_element.query_selector("text=/.*층/")
                if floor_match:
                    floor_text = await floor_match.inner_text()
            
            # '저/중/고'인 경우 상세 페이지로 이동
            if floor_text and floor_text.strip() in ["저", "중", "고"]:
                # 매물 클릭
                await property_element.click()
                await self.wait_random(1.5, 2.5)
                
                # 상세 페이지에서 층수 정보 가져오기
                property_info['층수'] = await self.extract_floor_info(page, floor_text)
                
                # 뒤로 가기
                await page.go_back()
                await self.wait_random(1.0, 2.0)
            else:
                property_info['층수'] = floor_text.strip() if floor_text else ""
            
            return property_info
            
        except Exception as e:
            print(f"매물 정보 추출 중 오류: {e}")
            return None
    
    async def crawl(self):
        """크롤링 메인 함수"""
        async with async_playwright() as p:
            # 브라우저 실행
            browser = await p.chromium.launch(
                headless=False,  # 디버깅을 위해 False로 설정 (필요시 True로 변경)
                slow_mo=500  # 동작을 천천히 (차단 방지)
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            
            try:
                # 네이버 부동산 페이지 접속
                print(f"페이지 접속 중: {self.url}")
                await page.goto(self.url, wait_until='networkidle')
                await self.wait_random(2.0, 4.0)
                
                # 매물 목록 로딩 대기
                print("매물 목록 로딩 대기 중...")
                await page.wait_for_selector("[class*='item'], [class*='매물'], [class*='list']", timeout=10000)
                await self.wait_random(1.0, 2.0)
                
                # 매물 목록 요소 찾기
                # 네이버 부동산의 실제 구조에 맞게 선택자 수정 필요
                property_items = await page.query_selector_all(
                    "[class*='item_card'], [class*='item'], [data-testid*='item']"
                )
                
                if not property_items:
                    # 다른 선택자 시도
                    property_items = await page.query_selector_all("a[href*='/articles/']")
                
                print(f"발견된 매물 수: {len(property_items)}")
                
                # 각 매물 정보 수집
                for idx, item in enumerate(property_items, 1):
                    print(f"매물 {idx}/{len(property_items)} 처리 중...")
                    
                    property_info = await self.get_property_details(page, item)
                    
                    if property_info:
                        self.results.append(property_info)
                        print(f"  - 동: {property_info['동']}, 가격: {property_info['가격']}, "
                              f"면적: {property_info['면적']}, 층수: {property_info['층수']}")
                    
                    # 매물 사이 랜덤 대기
                    await self.wait_random(1.5, 3.0)
                
            except Exception as e:
                print(f"크롤링 중 오류 발생: {e}")
                import traceback
                traceback.print_exc()
            
            finally:
                await browser.close()
    
    def save_to_csv(self, filename: str = "result.csv"):
        """결과를 CSV 파일로 저장"""
        if not self.results:
            print("저장할 데이터가 없습니다.")
            return
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            fieldnames = ['동', '가격', '면적', '층수']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in self.results:
                writer.writerow(result)
        
        print(f"\n총 {len(self.results)}개의 매물 정보가 {filename}에 저장되었습니다.")


async def main():
    """메인 실행 함수"""
    url = "https://new.land.naver.com/complexes/117804?ms=37.525766,126.967857,17&a=APT:PRE:ABYG:JGC&b=A1&e=RETAIL"
    
    crawler = NaverEstateCrawler(url)
    
    print("=" * 50)
    print("네이버 부동산 크롤링 시작")
    print("=" * 50)
    
    await crawler.crawl()
    
    print("\n" + "=" * 50)
    print("크롤링 완료")
    print("=" * 50)
    
    crawler.save_to_csv("result.csv")


if __name__ == "__main__":
    asyncio.run(main())
