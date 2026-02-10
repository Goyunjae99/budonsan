"""
네이버 부동산 크롤러 로직
Playwright 정상 플로우 + 동일 컨텍스트 JSON API 수집
"""

import asyncio
import json
import random
import re
import traceback
from typing import List, Dict, Optional, Callable, Tuple
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from playwright.async_api import async_playwright, Page, Request, Response


class NaverEstateCrawler:
    """네이버 부동산 크롤러 클래스"""
    
    def __init__(self, url: str, 
                 progress_callback: Optional[Callable] = None,
                 log_callback: Optional[Callable] = None,
                 property_found_callback: Optional[Callable] = None,
                 min_wait: float = 1.0,
                 max_wait: float = 3.0,
                 headless: bool = False):
        # 콜백은 가장 먼저 설정 (초기 로그 호출 시 AttributeError 방지)
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.property_found_callback = property_found_callback
        self.min_wait = min_wait
        self.max_wait = max_wait
        self.headless = headless
        self.is_cancelled = False
        self.results: List[Dict[str, str]] = []
        
        # URL에서 쿼리 파라미터 제거 (단지 메인 URL만 사용)
        self.base_url = self._clean_url(url)
        
        # Playwright 컨텍스트/페이지
        self._playwright = None
        self._context = None
        self._page = None

        self._warmup_url = "https://new.land.naver.com"
        self._fin_entry_url = (
            "https://fin.land.naver.com/complexes/117804"
            "?tab=article&articleTradeTypes=A1&tradeType=A1"
        )
        self._fin_api_url = "https://fin.land.naver.com/front-api/v1/complex/article/list"
        self._default_user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        self._max_nav_retries = 3

        # list 응답 캡처 (현재 미사용)
        self._list_responses: List[Dict] = []
        self._seen_article_ids = set()
        self._stop_on_429 = False
        
    def _clean_url(self, url: str) -> str:
        """URL에서 쿼리 파라미터 제거하여 단지 메인 URL만 반환"""
        parsed = urlparse(url)
        # 쿼리 파라미터 제거
        clean_parsed = parsed._replace(query='', fragment='')
        clean_url = urlunparse(clean_parsed)
        self._log(f"원본 URL: {url}")
        self._log(f"정리된 URL: {clean_url}")
        return clean_url
    
    def _extract_complex_id(self, url: str) -> Optional[str]:
        """URL에서 단지 ID 추출"""
        match = re.search(r'/complexes/(\d+)', url)
        if match:
            return match.group(1)
        return None
        
    def _log(self, message: str):
        """로그 메시지 출력"""
        log_callback = getattr(self, "log_callback", None)
        if log_callback:
            log_callback(message)
            return
        print(message)
    
    def _progress(self, current: int, total: int, message: str = ""):
        """진행 상황 업데이트"""
        if self.progress_callback:
            self.progress_callback(current, total, message)
    
    async def _setup_playwright_session(self):
        """Playwright로 세션 워밍업 및 검색 기반 단지 이동"""
        self._log("=" * 50)
        self._log("1단계: Playwright 세션 확보 시작")
        self._log("=" * 50)

        try:
            # launch_persistent_context 사용 (세션/쿠키 재사용)
            context = await self._playwright.chromium.launch_persistent_context(
                user_data_dir="./playwright_data",
                headless=self.headless,
                channel="chrome",  # 실제 크롬 사용
                locale="ko-KR",
                timezone_id="Asia/Seoul",
                viewport={'width': 1920, 'height': 1080},
                user_agent=self._default_user_agent
            )

            self._log("✓ Playwright 컨텍스트 생성 완료")
            context.on("close", lambda: self._log("⚠ context closed 이벤트 감지"))

            page = await context.new_page()
            self._context = context
            self._page = page
            self._log("✓ Playwright 페이지 생성 완료")
            page.on("close", lambda: self._log("⚠ page closed 이벤트 감지"))
            page.on("response", self._log_redirects)

            # 1) 워밍업: new.land 메인 접속
            self._log(f"워밍업 접속: {self._warmup_url}")
            self._progress(5, 100, "Playwright 세션 확보 중...")

            response = await self._safe_goto(page, self._warmup_url)

            if response and response.status == 404:
                self._log("⚠ 경고: 404 응답 받음. 잠시 대기 후 재시도...")
                await asyncio.sleep(3)
                response = await page.goto(self._warmup_url, wait_until='networkidle', timeout=30000)

            if response and response.status != 200:
                self._log(f"⚠ 경고: HTTP {response.status} 응답")

            await asyncio.sleep(2)

            # 2) fin.land 단지 페이지 이동
            self._log(f"단지 페이지 이동: {self._fin_entry_url}")
            response = await self._safe_goto(page, self._fin_entry_url)
            await asyncio.sleep(1.5)
            self._log(f"최종 page.url: {page.url}")
            if await self._is_404_page(page):
                self._log("✗ 404 감지. fin.land 단지 페이지 진입 실패")
                return False

            # 3) list 응답 캡처 리스너 등록
            self._attach_list_response_listener(page)

            # 4) 매물 탭/필터 1회 클릭
            await self._try_trigger_article_api(page)

            # 5) list 응답 1회 캡처 (30초)
            try:
                list_resp = await page.wait_for_response(
                    lambda r: r.url == self._fin_api_url and r.status == 200,
                    timeout=30000
                )
                data = await list_resp.json()
                self._list_responses.append(data)
                self._log("list 200 captured")
            except Exception:
                self._log("list 응답 30초 내 미발견. 수집 중단")
                return False

            self._log("✓ 세션 워밍업 및 단지 이동 완료")
            self._log("=" * 50)
            return True

        except Exception as e:
            self._log(f"✗ Playwright 세션 확보 실패: {e}")
            self._log(traceback.format_exc())
            return False

    async def _try_trigger_article_api(self, page: Page):
        """매물 탭/필터 1회 클릭 시도 (정상 플로우 유도)"""
        selectors = [
            "text=매물",
            "text=매매",
            "text=전세",
            "[data-testid*='tab'] >> text=매물",
            "[role='tab'] >> text=매물",
        ]
        for selector in selectors:
            try:
                elem = await page.query_selector(selector)
                if elem:
                    await elem.click()
                    await asyncio.sleep(1)
                    self._log("✓ 매물 탭/필터 클릭 성공")
                    return
            except Exception:
                continue
        self._log("매물 탭/필터 클릭은 생략됨")

    async def _recreate_context(self):
        """컨텍스트 재생성 (UA 변경 없음)"""
        if self._page:
            try:
                await self._page.close()
            except Exception:
                pass
        if self._context:
            try:
                await self._context.close()
            except Exception:
                pass
        context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir="./playwright_data",
            headless=self.headless,
            channel="chrome",
            locale="ko-KR",
            timezone_id="Asia/Seoul",
            viewport={'width': 1920, 'height': 1080},
            user_agent=self._default_user_agent
        )
        self._context = context
        page = await context.new_page()
        self._page = page
        self._log("✓ 컨텍스트 재생성 완료")
        page.on("response", self._log_redirects)

    async def _safe_goto(self, page: Page, url: str):
        """안전한 페이지 이동 (간단 재시도)"""
        last_response = None
        for attempt in range(1, self._max_nav_retries + 1):
            try:
                last_response = await page.goto(
                    url, wait_until="domcontentloaded", timeout=30000
                )
                await asyncio.sleep(1.0 + attempt * 0.3)
                if not await self._is_404_page(page):
                    return last_response
            except Exception:
                await asyncio.sleep(1.0 + attempt * 0.5)
        return last_response

    async def _is_404_page(self, page: Page) -> bool:
        """404 페이지 여부 감지"""
        try:
            url = page.url or ""
            if "/404" in url:
                return True
            title = await page.title()
            if "찾을 수 없" in title or "404" in title:
                return True
            body_text = await page.text_content("body")
            if body_text and ("찾을 수 없" in body_text or "/404" in body_text):
                return True
        except Exception:
            return False
        return False

    async def _extract_list_items(self, page: Page):
        """리스트 아이템 요소 수집"""
        selectors = [
            "a[href*='/articles/']",
            "[class*='item'][href*='/articles/']",
            "[class*='item_card'] a[href*='/articles/']",
        ]
        for sel in selectors:
            try:
                items = await page.query_selector_all(sel)
                if items:
                    return items
            except Exception:
                continue
        return []

    async def _extract_floor_from_detail_table(self, page: Page) -> str:
        """우측 상세정보 테이블에서 층수/해당층 추출"""
        try:
            labels = await page.query_selector_all("dt, th, .label")
            for label in labels:
                text = (await label.inner_text()).strip()
                if "층수" in text or "해당층" in text:
                    # 인접한 dd/td 또는 다음 형제에서 값 추출
                    value = await label.evaluate(
                        """(el) => {
                            const dd = el.nextElementSibling;
                            if (dd) return dd.innerText;
                            const parent = el.parentElement;
                            if (parent && parent.nextElementSibling) return parent.nextElementSibling.innerText;
                            return "";
                        }"""
                    )
                    if value:
                        return value.strip()
        except Exception:
            return ""
        return ""

    def _log_redirects(self, response: Response):
        """리다이렉트 로그"""
        try:
            status = response.status
            if 300 <= status < 400:
                location = response.headers.get("location")
                self._log(f"리다이렉트: {response.url} -> {location}")
        except Exception:
            return

    def _attach_list_response_listener(self, page: Page):
        """list API 응답 캡처 리스너 등록"""
        async def handle_response(response: Response):
            try:
                url = response.url
                if url == self._fin_api_url:
                    status = response.status
                    if status == 429:
                        self._log("⚠ 429 발생, 더보기/스크롤 중단")
                        self._stop_on_429 = True
                        return
                    if status != 200:
                        return
                    data = await response.json()
                    self._list_responses.append(data)
            except Exception:
                return

        page.on("response", handle_response)
    
    def _parse_property_data(self, item: Dict) -> Optional[Dict[str, str]]:
        """JSON 데이터에서 매물 정보 추출"""
        try:
            property_info = {
                '동': '',
                '가격': '',
                '면적': '',
                '층수': ''
            }
            
            # 동 정보 추출
            dong = item.get('dongName') or item.get('dong') or item.get('buildingName') or ''
            if dong:
                property_info['동'] = str(dong).strip()
            
            # 가격 정보 추출
            price = item.get('dealOrWarrantPrc') or item.get('price') or item.get('dealPrice') or ''
            if price:
                # 숫자 형식인 경우 포맷팅
                try:
                    price_num = int(price)
                    if price_num >= 10000:
                        eok = price_num // 10000
                        man = price_num % 10000
                        if man > 0:
                            property_info['가격'] = f"{eok}억 {man:,}만원"
                        else:
                            property_info['가격'] = f"{eok}억원"
                    else:
                        property_info['가격'] = f"{price_num:,}만원"
                except:
                    property_info['가격'] = str(price).strip()
            
            # 면적 정보 추출
            area = item.get('area1') or item.get('area') or item.get('exclusiveArea') or ''
            if area:
                try:
                    area_num = float(area)
                    property_info['면적'] = f"{area_num:.2f}㎡"
                except:
                    property_info['면적'] = str(area).strip()
            
            # 층수 정보 추출
            floor = item.get('floor') or item.get('floorInfo') or ''
            total_floor = item.get('totalFloor') or item.get('maxFloor') or ''
            
            if floor and total_floor:
                try:
                    floor_num = int(floor)
                    total_num = int(total_floor)
                    property_info['층수'] = f"{floor_num}/{total_num}층"
                except:
                    property_info['층수'] = str(floor).strip()
            elif floor:
                property_info['층수'] = str(floor).strip()
            
            return property_info
            
        except Exception as e:
            self._log(f"매물 데이터 파싱 오류: {e}")
            return None
    
    def _build_api_url(self, base_url: str, page: int, page_size: int) -> str:
        """API URL에 페이지 파라미터를 안전하게 구성"""
        parsed = urlparse(base_url)
        query = parse_qs(parsed.query)
        query["page"] = [str(page)]
        query["pageSize"] = [str(page_size)]
        new_query = urlencode(query, doseq=True)
        return urlunparse(parsed._replace(query=new_query))

    def _force_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """필수 헤더 강제 덮어쓰기"""
        merged = dict(headers or {})
        merged["Origin"] = self._fin_origin
        merged["Referer"] = self._fin_referer
        merged["User-Agent"] = self._fin_user_agent
        merged["Accept"] = "application/json"
        merged["Content-Type"] = "application/json"
        return merged

    async def _log_cookie_presence(self):
        """쿠키 포함 여부 로그"""
        try:
            cookies = await self._context.cookies(self._fin_origin)
            self._log(f"쿠키 개수(컨텍스트): {len(cookies)}")
        except Exception:
            self._log("쿠키 확인 실패")

    def _is_context_alive(self) -> bool:
        """page/context 생존 여부"""
        try:
            if not self._context or not self._page:
                return False
            if self._page.is_closed():
                return False
            return True
        except Exception:
            return False

    def _log_http_issue(self, url: str, status: Optional[int], headers: Dict[str, str]):
        retry_after = headers.get("retry-after")
        alive = self._is_context_alive()
        self._log(
            f"HTTP 오류 - url={url}, status={status}, retry-after={retry_after}, "
            f"context_alive={alive}"
        )

    def _find_key_paths(self, data: object, key: str, path: Optional[List[str]] = None):
        """JSON에서 특정 키의 경로와 값을 탐색"""
        if path is None:
            path = []
        results = []
        if isinstance(data, dict):
            for k, v in data.items():
                new_path = path + [k]
                if k == key:
                    results.append((new_path, v))
                results.extend(self._find_key_paths(v, key, new_path))
        elif isinstance(data, list):
            for idx, item in enumerate(data):
                new_path = path + [f"[{idx}]"]
                results.extend(self._find_key_paths(item, key, new_path))
        return results

    def _pick_value_by_key(self, data: Dict, key: str):
        """JSON에서 특정 키 값과 경로 선택"""
        candidates = self._find_key_paths(data, key)
        if not candidates:
            return None, None
        # 우선 비어있지 않은 값 선택
        for path, value in candidates:
            if value not in (None, "", [], {}):
                return value, ".".join(path)
        # 모두 비어있다면 첫 번째
        value, path = candidates[0]
        return value, ".".join(path)

    async def _fetch_json_via_context(
        self,
        url: str,
        headers: Dict[str, str],
        method: str = "GET",
        payload: Optional[Dict] = None
    ) -> Tuple[Optional[Dict], Optional[int], Dict[str, str], str]:
        """Playwright 컨텍스트 요청으로 JSON 가져오기"""
        try:
            if url.startswith(self._fin_api_url):
                merged_headers = self._force_headers(headers)
            else:
                merged_headers = dict(headers or {})
            if method.upper() == "POST":
                body = json.dumps(payload or {}, ensure_ascii=False)
                response = await self._context.request.post(
                    url, headers=merged_headers, data=body, timeout=30000
                )
            else:
                response = await self._context.request.get(url, headers=merged_headers, timeout=30000)
            status = response.status
            resp_headers = response.headers or {}
            text = ""
            try:
                text = await response.text()
            except Exception:
                text = ""

            if not self._cookie_logged:
                try:
                    req_headers = response.request.headers
                    has_cookie = "cookie" in {k.lower(): v for k, v in req_headers.items()}
                    self._log(f"요청 쿠키 포함 여부: {has_cookie}")
                except Exception:
                    await self._log_cookie_presence()
                self._cookie_logged = True

            try:
                text_preview = text[:300]
                self._log(f"API 응답 status={status}, body_preview={text_preview}")
            except Exception:
                self._log(f"API 응답 status={status}, body_preview=unavailable")
            if status == 200:
                data = await response.json()
                return data, status, resp_headers, text
            return None, status, resp_headers, text
        except Exception as e:
            self._log(f"✗ 컨텍스트 요청 오류: {e}")
            return None, None, {}, ""

    async def _request_with_retry(
        self,
        url: str,
        headers: Dict[str, str],
        method: str = "GET",
        payload: Optional[Dict] = None,
        max_retries: int = 5
    ) -> Optional[Dict]:
        """401/404/429 대응 포함 Playwright 컨텍스트 요청 재시도 로직"""
        attempt = 0
        cooldown_min = 120
        cooldown_max = 300

        while not self.is_cancelled:
            data, status, resp_headers, _text = await self._fetch_json_via_context(
                url, headers, method=method, payload=payload
            )

            if status == 200 and data is not None:
                return data

            self._log_http_issue(url, status, resp_headers)

            if status == 401:
                await asyncio.sleep(2)
            elif status == 404:
                await asyncio.sleep(2)
            elif status == 429:
                retry_after = resp_headers.get("retry-after")
                if retry_after:
                    try:
                        wait_sec = int(float(retry_after))
                    except Exception:
                        wait_sec = 10
                    self._log(f"⚠ 429 발생. Retry-After={wait_sec}s 대기 후 재시도...")
                    await asyncio.sleep(wait_sec)
                else:
                    backoff = min(2 ** attempt, 60) + random.uniform(0.5, 2.0)
                    self._log(f"⚠ 429 발생. 백오프 {backoff:.1f}s 대기...")
                    await asyncio.sleep(backoff)
            else:
                await asyncio.sleep(2)

            attempt += 1
            if attempt > max_retries:
                cooldown = random.uniform(cooldown_min, cooldown_max)
                self._log(f"⚠ 재시도 한도 초과. 쿨다운 {int(cooldown)}s 후 재시도...")
                await asyncio.sleep(cooldown)
                attempt = 0

        return None

    async def _request_with_retry_meta(
        self,
        url: str,
        headers: Dict[str, str],
        method: str = "GET",
        payload: Optional[Dict] = None,
        max_retries: int = 3
    ) -> Tuple[Optional[Dict], Optional[int], Dict[str, str], str]:
        """메타 정보 포함 재시도 요청"""
        attempt = 0
        while not self.is_cancelled:
            data, status, resp_headers, text = await self._fetch_json_via_context(
                url, headers, method=method, payload=payload
            )
            if status == 200 and data is not None:
                return data, status, resp_headers, text

            self._log_http_issue(url, status, resp_headers)
            await asyncio.sleep(2)
            attempt += 1
            if attempt > max_retries:
                return data, status, resp_headers, text

        return None, None, {}, ""

    async def _request_once(
        self,
        url: str,
        headers: Dict[str, str],
        method: str = "GET",
        payload: Optional[Dict] = None
    ) -> Tuple[Optional[Dict], Optional[int], Dict[str, str], str]:
        """재시도 없이 1회 요청"""
        return await self._fetch_json_via_context(url, headers, method=method, payload=payload)

    def _extract_floor_from_detail_json(self, detail: Dict) -> str:
        """상세 JSON에서 층수/전체층 추출"""
        if not detail:
            return ""
        floor = detail.get("floor") or detail.get("floorInfo") or ""
        total = detail.get("totalFloor") or detail.get("maxFloor") or ""
        if isinstance(floor, (int, float)) and isinstance(total, (int, float)):
            return f"{int(floor)}/{int(total)}층"
        if isinstance(floor, str) and "/" in floor and "층" in floor:
            return floor.strip()
        if floor and total:
            return f"{floor}/{total}층"
        return ""

    async def _fetch_article_detail(self, article_no: str) -> Optional[Dict]:
        """상세 JSON API 호출"""
        detail_url = f"https://new.land.naver.com/api/articles/{article_no}"
        return await self._request_with_retry(detail_url, self.api_headers, method="GET")
    
    async def crawl(self):
        """크롤링 메인 함수"""
        self.is_cancelled = False
        self.results = []

        # Playwright 시작 (스레드 내부에서 생성/유지)
        self._log("Playwright 시작 중...")
        self._playwright = await async_playwright().start()
        
        # 1단계: Playwright로 세션 확보
        self._progress(0, 100, "Playwright 세션 확보 중...")
        session_success = await self._setup_playwright_session()
        
        if not session_success:
            self._log("✗ 세션 확보 실패. 크롤링을 중단합니다.")
            self._progress(0, 0, "세션 확보 실패")
            return
        
        if self.is_cancelled:
            return
        
        # 2단계: DOM 리스트/상세 기반 수집
        self._log("=" * 50)
        self._log("2단계: DOM 리스트/상세 기반 매물 수집 시작")
        self._log("=" * 50)
        
        self._progress(10, 100, "매물 데이터 수집 중...")

        await asyncio.sleep(2)

        items = await self._extract_list_items(self._page)
        if not items:
            self._log("매물 리스트를 찾지 못했습니다.")
            await self._close_context("no_list")
            return

        total_items = len(items)
        total_collected = 0
        for idx, item in enumerate(items, 1):
            if self.is_cancelled:
                break

            self._log(f"매물 {idx}/{total_items} 처리 중...")
            self._progress(
                int(10 + (idx / max(1, total_items)) * 85),
                100,
                f"매물 {idx}/{total_items} 처리 중..."
            )

            try:
                text = await item.inner_text()
            except Exception:
                text = ""

            dong = ""
            price = ""
            area = ""
            floor = ""

            dong_match = re.search(r"\d+동", text)
            if dong_match:
                dong = dong_match.group(0)

            area_match = re.search(r"\d+(\.\d+)?㎡", text)
            if area_match:
                area = area_match.group(0)

            price_match = re.search(r"\d+억\s?\d*,?\d*만원|\d+억|\d+만원", text)
            if price_match:
                price = price_match.group(0)

            floor_match = re.search(r"\d+/\d+층|저|중|고", text)
            if floor_match:
                floor = floor_match.group(0)

            # 상세 패널에서 층수/해당층 파싱
            try:
                await item.click()
                await self._page.wait_for_load_state("networkidle")
                await asyncio.sleep(0.8)
                detail_floor = await self._extract_floor_from_detail_table(self._page)
                if detail_floor:
                    floor = detail_floor
            except Exception:
                self._log("상세 패널 파싱 실패, 리스트 값 사용")

            property_info = {
                "동": dong,
                "가격": price,
                "면적": area,
                "층수": floor,
            }

            self.results.append(property_info)
            total_collected += 1
            self._log(
                f"  ✓ [{total_collected}] 동: {dong}, 가격: {price}, 면적: {area}, 층수: {floor}"
            )
            if self.property_found_callback:
                self.property_found_callback(property_info)

            await asyncio.sleep(random.uniform(self.min_wait, self.max_wait))
        
        if not self.is_cancelled:
            self._progress(100, 100, "크롤링 완료")
            self._log("=" * 50)
            self._log(f"총 {len(self.results)}개의 매물 정보를 수집했습니다.")
            self._log("=" * 50)
        else:
            self._log("크롤링이 중지되었습니다.")

        # 컨텍스트 정리 (정상 종료 또는 중지 시점에만)
        await self._close_context("crawl_end")
    
    def cancel(self):
        """크롤링 취소"""
        self.is_cancelled = True
        self._log("크롤링 취소 요청됨...")

    async def _close_context(self, reason: str):
        """컨텍스트/페이지 종료 (조건부)"""
        self._log(f"컨텍스트 종료 요청: {reason}")
        self._log("".join(traceback.format_stack(limit=6)))

        if self._page:
            try:
                await self._page.close()
            except Exception:
                pass
            self._page = None

        if self._context:
            try:
                await self._context.close()
            except Exception:
                pass
            self._context = None

        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
            self._playwright = None
