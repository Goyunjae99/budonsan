"""
데이터 처리 유틸리티
"""

from typing import List, Dict


def calculate_statistics(data: List[Dict[str, str]]) -> Dict[str, any]:
    """
    매물 데이터의 통계 정보 계산
    
    Args:
        data: 매물 데이터 리스트
        
    Returns:
        통계 정보 딕셔너리
    """
    stats = {
        'total': len(data),
        'min_price': '',
        'max_price': '',
        'avg_price': '',
        'dong_count': {}
    }
    
    if not data:
        return stats
    
    # 동별 매물 수 계산
    for item in data:
        dong = item.get('동', '미지정')
        stats['dong_count'][dong] = stats['dong_count'].get(dong, 0) + 1
    
    # 가격 정보 추출 (간단한 파싱)
    prices = []
    for item in data:
        price_str = item.get('가격', '')
        if price_str:
            prices.append(price_str)
    
    if prices:
        stats['min_price'] = min(prices, key=lambda x: len(x))
        stats['max_price'] = max(prices, key=lambda x: len(x))
    
    return stats


def filter_data(data: List[Dict[str, str]], search_text: str) -> List[Dict[str, str]]:
    """
    데이터 필터링
    
    Args:
        data: 원본 데이터
        search_text: 검색어
        
    Returns:
        필터링된 데이터
    """
    if not search_text:
        return data
    
    search_text = search_text.lower()
    filtered = []
    
    for item in data:
        # 모든 필드에서 검색
        for key, value in item.items():
            if search_text in str(value).lower():
                filtered.append(item)
                break
    
    return filtered
