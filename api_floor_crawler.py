import json
import time
import random
from typing import Any, Dict, List, Optional, Tuple

import requests
import pandas as pd


# -----------------------------
# 1) 공통: 세션 + 헤더 구성
# -----------------------------
UA_MOBILE = (
    "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/144.0.0.0 Mobile Safari/537.36"
)

REFERER = "https://fin.land.naver.com/complexes/117804?tab=article&transactionPyeongTypeNumber=4&transactionTradeType=A1"
ORIGIN = "https://fin.land.naver.com"

BASE_HEADERS = {
    "User-Agent": UA_MOBILE,
    "Referer": REFERER,
    "Origin": ORIGIN,
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json;charset=UTF-8",
    # 필요 시 아래를 추가해볼 수 있음(서버가 민감하게 볼 때가 있음)
    # "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}


def make_session(cookie_string: Optional[str] = None) -> requests.Session:
    s = requests.Session()
    s.headers.update(BASE_HEADERS)
    if cookie_string:
        # 쿠키 문자열을 그대로 넣을 수도 있지만, 만료/변형이 잦아 권장되진 않음
        s.headers.update({"Cookie": cookie_string})
    return s


def warm_up_session(s: requests.Session) -> None:
    """
    404/차단을 줄이기 위해 referer 페이지를 한 번 GET 해서
    서버가 요구하는 쿠키/세션 컨텍스트를 맞춘다.
    """
    try:
        r = s.get(REFERER, timeout=15, allow_redirects=True)
        # 응답 코드 확인용(디버깅 시 print)
        # print("warmup:", r.status_code, r.url)
    except Exception:
        pass


# -----------------------------
# 2) 매물 목록 호출 (POST)
# -----------------------------
LIST_ENDPOINT_CANDIDATES = [
    "https://fin.land.naver.com/front-api/v1/complex/article/list",
    # 가끔 호스트가 바뀌는 케이스 대비(후보)
    "https://fin.land.naver.com/front-api/v1/complex/article/list",
]


def post_json_with_fallback(
    s: requests.Session,
    payload: Dict[str, Any],
    timeout: int = 20,
) -> Tuple[str, requests.Response]:
    """
    엔드포인트 후보를 순차로 시도해서 404를 회피.
    """
    last_exc = None
    for url in LIST_ENDPOINT_CANDIDATES:
        try:
            r = s.post(url, data=json.dumps(payload), timeout=timeout)
            if r.status_code != 404:
                return url, r
        except Exception as e:
            last_exc = e
            continue
    if last_exc:
        raise last_exc
    # 모두 404면 마지막 응답을 반환
    return LIST_ENDPOINT_CANDIDATES[-1], r  # type: ignore


def extract_article_list(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    응답 JSON 구조가 바뀔 수 있어서 여러 케이스로 방어.
    """
    # 흔한 케이스들 후보
    for key_path in [
        ("articleList",),
        ("result", "articleList"),
        ("data", "articleList"),
        ("result", "list"),
        ("data", "list"),
    ]:
        cur: Any = data
        ok = True
        for k in key_path:
            if isinstance(cur, dict) and k in cur:
                cur = cur[k]
            else:
                ok = False
                break
        if ok and isinstance(cur, list):
            return cur
    return []


# -----------------------------
# 3) 상세 정보로 "진짜 층수" 시도
# -----------------------------
def fetch_basic_info(
    s: requests.Session,
    article_id: str,
    real_estate_type: Optional[str],
    trade_type: Optional[str],
) -> Optional[Dict[str, Any]]:
    """
    글에서 확인되는 패턴: /front-api/v1/article/basicInfo?articleId=...&realEstateType=...&tradeType=...
    (실제 파라미터 명은 응답/프론트에 따라 달라질 수 있어 방어적으로 처리)
    """
    if not real_estate_type or not trade_type:
        return None

    url = (
        "https://fin.land.naver.com/front-api/v1/article/basicInfo"
        f"?articleId={article_id}&realEstateType={real_estate_type}&tradeType={trade_type}"
    )
    r = s.get(url, timeout=20)
    if r.status_code != 200:
        return None
    try:
        return r.json()
    except Exception:
        return None


def guess_exact_floor_from_basic_info(basic: Dict[str, Any]) -> Optional[str]:
    """
    API마다 필드명이 다를 수 있어서, '숫자 층' 후보들을 넓게 탐색.
    발견 시 가장 그럴듯한 값을 반환.
    """
    # 자주 나오는 후보 키들(경험적으로 많이 쓰임)
    candidate_keys = [
        "flrNo", "floorNo", "floor", "articleFloor", "bldgFloor",
        "layerNo", "flr", "dongFloor", "hoFloor"
    ]

    # dict 깊게 훑기
    def walk(obj: Any) -> List[Tuple[str, Any]]:
        found = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                found.append((k, v))
                found.extend(walk(v))
        elif isinstance(obj, list):
            for it in obj:
                found.extend(walk(it))
        return found

    for k, v in walk(basic):
        if k in candidate_keys:
            # 숫자/문자 모두 처리
            if isinstance(v, (int, float)) and v > 0:
                return str(int(v))
            if isinstance(v, str) and v.strip():
                # "12" 같은 문자열이면 그대로
                return v.strip()

    return None


# -----------------------------
# 4) 실행: 목록 -> 출력 -> DF
# -----------------------------
def main():
    cookie_string = """NNB=VV367CBWHAGGQ; ASID=79a029cd000001967092e70f00000058; ...; BUC=xIC7-2dWkggQwx_WzWqWGOwmeQxyeWbL_ZtAli9A744=""".strip()
    # 위 쿠키는 그대로 쓸 수도 있지만, 만료 가능성이 높아서 warm-up을 반드시 같이 돌리는 걸 추천

    s = make_session(cookie_string=cookie_string)
    warm_up_session(s)

    payload = {
        "size": 30,
        "complexNumber": "117804",
        "tradeTypes": [],
        "pyeongTypes": [],
        "dongNumbers": [],
        "userChannelType": "MOBILE",
        "articleSortType": "RANKING_DESC",
        # lastInfo는 상황에 따라 필요/불필요가 갈릴 수 있어 초기엔 빼고 시작해도 됨
        "lastInfo": [1, 930, "2608019513"],
    }

    used_url, resp = post_json_with_fallback(s, payload)
    print("LIST endpoint used:", used_url)
    print("STATUS:", resp.status_code)

    if resp.status_code != 200:
        # 디버깅 정보
        print(resp.text[:500])
        raise SystemExit("목록 API 호출 실패")

    data = resp.json()
    articles = extract_article_list(data)
    print("articleList count:", len(articles))

    rows = []
    for a in articles:
        # 필드명은 실제 응답에 맞춰 조정 필요
        article_id = str(a.get("articleId") or a.get("id") or "")
        name = a.get("articleName") or a.get("name") or a.get("aptName") or ""
        flr_info = a.get("flrInfo") or a.get("floorInfo") or ""

        # 목록 출력(요청사항)
        print(f"- {name} | flrInfo={flr_info} | articleId={article_id}")

        real_estate_type = a.get("realEstateType")  # 예: A02
        trade_type = a.get("tradeType")             # 예: A1

        exact_floor = None
        # flrInfo가 "저/중/고/총층" 형태면 상세로 진짜 층수 시도
        if isinstance(flr_info, str) and (flr_info.startswith("저/") or flr_info.startswith("중/") or flr_info.startswith("고/")):
            if article_id and real_estate_type and trade_type:
                # 과도 요청 방지용 랜덤 딜레이
                time.sleep(random.uniform(0.3, 0.9))

                basic = fetch_basic_info(s, article_id, real_estate_type, trade_type)
                if basic:
                    exact_floor = guess_exact_floor_from_basic_info(basic)

        rows.append({
            "articleId": article_id,
            "name": name,
            "flrInfo": flr_info,
            "realEstateType": real_estate_type,
            "tradeType": trade_type,
            "exactFloor_guess": exact_floor,  # None이면 상세에서도 못 찾은 케이스
        })

    df = pd.DataFrame(rows)
    print("\n=== DataFrame Preview ===")
    print(df.head(20))
    return df


if __name__ == "__main__":
    main()
