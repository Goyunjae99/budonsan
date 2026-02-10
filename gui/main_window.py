"""
메인 윈도우 GUI
"""

import sys
from datetime import datetime
from typing import List, Dict

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QProgressBar, QTextEdit, QTableWidget,
    QTableWidgetItem, QMessageBox, QFileDialog, QGroupBox, QHeaderView
)
from PySide6.QtCore import Qt, QThread
from PySide6.QtGui import QFont

from gui.crawler_thread import CrawlerThread
from utils.excel_exporter import save_to_excel, generate_default_filename
from utils.data_processor import calculate_statistics, filter_data


class MainWindow(QMainWindow):
    """메인 윈도우 클래스"""
    
    def __init__(self):
        super().__init__()
        self.crawler_thread = None
        self.property_data: List[Dict[str, str]] = []
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("네이버 부동산 매물 크롤러")
        self.setMinimumSize(1000, 700)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 제목
        title_label = QLabel("네이버 부동산 매물 크롤러")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 단지 정보 그룹
        info_group = QGroupBox("단지 정보")
        info_layout = QVBoxLayout()
        
        location_label = QLabel("지역: 서울시 용산구 한강로3가 센트럴파크")
        info_layout.addWidget(location_label)
        
        url_layout = QHBoxLayout()
        url_label = QLabel("URL:")
        self.url_input = QLineEdit()
        # 쿼리 파라미터 없는 단지 메인 URL만 사용
        self.url_input.setText(
            "https://new.land.naver.com/complexes/117804"
        )
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        info_layout.addLayout(url_layout)
        
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("크롤링 시작")
        self.start_button.clicked.connect(self.start_crawling)
        self.stop_button = QPushButton("중지")
        self.stop_button.clicked.connect(self.stop_crawling)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        info_layout.addLayout(button_layout)
        
        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)
        
        # 진행 상황 그룹
        progress_group = QGroupBox("진행 상황")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("대기 중...")
        progress_layout.addWidget(self.status_label)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        progress_layout.addWidget(self.log_text)
        
        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)
        
        # 매물 정보 테이블
        table_group = QGroupBox("매물 정보")
        table_layout = QVBoxLayout()
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["동", "가격", "면적", "층수"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSortingEnabled(True)
        table_layout.addWidget(self.table)
        
        table_group.setLayout(table_layout)
        main_layout.addWidget(table_group)
        
        # 통계 정보 및 버튼
        bottom_layout = QHBoxLayout()
        
        self.stats_label = QLabel("전체 매물: 0개")
        bottom_layout.addWidget(self.stats_label)
        
        bottom_layout.addStretch()
        
        self.excel_button = QPushButton("엑셀 저장")
        self.excel_button.clicked.connect(self.save_to_excel)
        self.excel_button.setEnabled(False)
        bottom_layout.addWidget(self.excel_button)
        
        self.csv_button = QPushButton("CSV 저장")
        self.csv_button.clicked.connect(self.save_to_csv)
        self.csv_button.setEnabled(False)
        bottom_layout.addWidget(self.csv_button)
        
        main_layout.addLayout(bottom_layout)
        
        # 초기 로그 메시지
        self.add_log("프로그램이 시작되었습니다.")
        self.add_log("URL을 확인하고 '크롤링 시작' 버튼을 클릭하세요.")
    
    def add_log(self, message: str):
        """로그 메시지 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        self.log_text.append(log_message)
        # 스크롤을 맨 아래로
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def update_progress(self, current: int, total: int, message: str):
        """진행 상황 업데이트"""
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
            self.status_label.setText(f"{message} ({percentage}%)")
        else:
            self.progress_bar.setValue(0)
            self.status_label.setText(message)
    
    def start_crawling(self):
        """크롤링 시작"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "경고", "URL을 입력해주세요.")
            return
        
        # URL에서 쿼리 파라미터 제거 (단지 메인 URL만 사용)
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(url)
        clean_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
        if clean_url != url:
            self.add_log(f"URL 정리: {url} -> {clean_url}")
            url = clean_url
        
        # UI 상태 변경
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.excel_button.setEnabled(False)
        self.csv_button.setEnabled(False)
        self.property_data = []
        self.table.setRowCount(0)
        self.stats_label.setText("전체 매물: 0개")
        
        # 크롤링 스레드 시작
        self.crawler_thread = CrawlerThread(url, min_wait=1.0, max_wait=3.0, headless=False)
        self.crawler_thread.progress_updated.connect(self.update_progress)
        self.crawler_thread.log_message.connect(self.add_log)
        self.crawler_thread.property_found.connect(self.add_property_to_table)
        self.crawler_thread.finished.connect(self.on_crawling_finished)
        self.crawler_thread.error_occurred.connect(self.on_crawling_error)
        self.crawler_thread.start()
        
        self.add_log("크롤링을 시작합니다...")
    
    def stop_crawling(self):
        """크롤링 중지"""
        if self.crawler_thread and self.crawler_thread.isRunning():
            self.crawler_thread.cancel()
            self.add_log("크롤링 중지 요청됨...")
            self.stop_button.setEnabled(False)
    
    def add_property_to_table(self, property_info: Dict[str, str]):
        """테이블에 매물 정보 추가"""
        self.property_data.append(property_info)
        
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        self.table.setItem(row, 0, QTableWidgetItem(property_info.get('동', '')))
        self.table.setItem(row, 1, QTableWidgetItem(property_info.get('가격', '')))
        self.table.setItem(row, 2, QTableWidgetItem(property_info.get('면적', '')))
        self.table.setItem(row, 3, QTableWidgetItem(property_info.get('층수', '')))
        
        # 통계 업데이트
        stats = calculate_statistics(self.property_data)
        self.stats_label.setText(f"전체 매물: {stats['total']}개")
    
    def on_crawling_finished(self, results: List[Dict[str, str]]):
        """크롤링 완료 처리"""
        self.property_data = results
        
        # UI 상태 복원
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.excel_button.setEnabled(True)
        self.csv_button.setEnabled(True)
        
        # 통계 업데이트
        stats = calculate_statistics(self.property_data)
        stats_text = f"전체 매물: {stats['total']}개"
        if stats['dong_count']:
            dong_info = ", ".join([f"{k}: {v}개" for k, v in stats['dong_count'].items()])
            stats_text += f" | 동별: {dong_info}"
        self.stats_label.setText(stats_text)
        
        self.add_log(f"크롤링이 완료되었습니다. 총 {len(results)}개의 매물 정보를 수집했습니다.")
        QMessageBox.information(self, "완료", f"크롤링이 완료되었습니다.\n총 {len(results)}개의 매물 정보를 수집했습니다.")
    
    def on_crawling_error(self, error_message: str):
        """크롤링 오류 처리"""
        self.add_log(f"오류 발생: {error_message}")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        QMessageBox.critical(self, "오류", f"크롤링 중 오류가 발생했습니다:\n{error_message}")
    
    def save_to_excel(self):
        """엑셀 파일로 저장"""
        if not self.property_data:
            QMessageBox.warning(self, "경고", "저장할 데이터가 없습니다.")
            return
        
        # 파일 저장 대화상자
        default_filename = generate_default_filename()
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "엑셀 파일 저장",
            default_filename,
            "Excel Files (*.xlsx);;All Files (*)"
        )
        
        if filename:
            if save_to_excel(self.property_data, filename):
                self.add_log(f"엑셀 파일이 저장되었습니다: {filename}")
                QMessageBox.information(self, "완료", f"엑셀 파일이 저장되었습니다:\n{filename}")
            else:
                QMessageBox.critical(self, "오류", "엑셀 파일 저장에 실패했습니다.")
    
    def save_to_csv(self):
        """CSV 파일로 저장"""
        if not self.property_data:
            QMessageBox.warning(self, "경고", "저장할 데이터가 없습니다.")
            return
        
        # 파일 저장 대화상자
        default_filename = f"센트럴파크_매물정보_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "CSV 파일 저장",
            default_filename,
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if filename:
            try:
                import csv
                with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                    fieldnames = ['동', '가격', '면적', '층수']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(self.property_data)
                
                self.add_log(f"CSV 파일이 저장되었습니다: {filename}")
                QMessageBox.information(self, "완료", f"CSV 파일이 저장되었습니다:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "오류", f"CSV 파일 저장에 실패했습니다:\n{str(e)}")
