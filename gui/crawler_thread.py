"""
크롤링 스레드 클래스
GUI 스레드와 분리하여 크롤링 작업 수행
"""

from PySide6.QtCore import QThread, Signal
from crawler.naver_crawler import NaverEstateCrawler
from typing import List, Dict


class CrawlerThread(QThread):
    """크롤링 작업을 수행하는 스레드"""
    
    # 시그널 정의
    progress_updated = Signal(int, int, str)  # current, total, message
    log_message = Signal(str)  # log message
    property_found = Signal(dict)  # property info
    finished = Signal(list)  # results
    error_occurred = Signal(str)  # error message
    
    def __init__(self, url: str, min_wait: float = 1.0, max_wait: float = 3.0, headless: bool = False):
        super().__init__()
        self.url = url
        self.min_wait = min_wait
        self.max_wait = max_wait
        self.headless = headless
        self.crawler = None
        
    def run(self):
        """스레드 실행"""
        try:
            # 크롤러 생성
            self.crawler = NaverEstateCrawler(
                url=self.url,
                progress_callback=self._on_progress,
                log_callback=self._on_log,
                property_found_callback=self._on_property_found,
                min_wait=self.min_wait,
                max_wait=self.max_wait,
                headless=self.headless
            )
            
            # 비동기 크롤링 실행
            import asyncio
            asyncio.run(self.crawler.crawl())
            
            # 완료 시그널 전송
            self.finished.emit(self.crawler.results)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
            import traceback
            self.log_message.emit(traceback.format_exc())
    
    def _on_progress(self, current: int, total: int, message: str = ""):
        """진행 상황 콜백"""
        self.progress_updated.emit(current, total, message)
    
    def _on_log(self, message: str):
        """로그 콜백"""
        self.log_message.emit(message)
    
    def _on_property_found(self, property_info: dict):
        """매물 발견 콜백"""
        self.property_found.emit(property_info)
    
    def cancel(self):
        """크롤링 취소"""
        if self.crawler:
            self.crawler.cancel()
