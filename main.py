"""
네이버 부동산 매물 크롤러 GUI 프로그램
메인 진입점
"""

import sys
from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow


def main():
    """메인 함수"""
    app = QApplication(sys.argv)
    
    # 애플리케이션 정보 설정
    app.setApplicationName("네이버 부동산 매물 크롤러")
    app.setOrganizationName("EstateCrawler")
    
    # 메인 윈도우 생성 및 표시
    window = MainWindow()
    window.show()
    
    # 이벤트 루프 실행
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
