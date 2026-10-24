"""키워드 경쟁강도 분석: 네이버 월간 검색량 vs 쇼핑 등록 상품 수.

필요한 환경변수:
  NAVER_AD_API_KEY, NAVER_AD_SECRET_KEY, NAVER_AD_CUSTOMER_ID  (네이버 검색광고 API)
  NAVER_CLIENT_ID, NAVER_CLIENT_SECRET                        (네이버 개발자센터 검색 API)

실행: python3 scripts/keyword_competition.py  → data/keyword_competition.csv
"""
import base64
import csv
import hashlib
import hmac
import json
import os
import sys
import time
import urllib.parse
import urllib.request

KEYWORDS = [
    # 이동
    "고양이 계단", "고양이 스텝", "노령묘 계단", "고양이 침대 계단", "고양이 미끄럼방지 매트",
    # 식사
    "고양이 높은 식기", "노령묘 식기", "고양이 식기 받침대", "수염 스트레스 식기", "고양이 정수기",
    # 화장실
    "노령묘 화장실", "낮은 고양이 화장실", "고양이 화장실 발판", "고양이 배변패드",
    # 휴식
    "노령묘 방석", "고양이 관절 쿠션", "고양이 메모리폼 방석", "고양이 보온 하우스",
    # 대표
    "노령묘 용품", "노령묘 케어",
]

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "keyword_competition.csv")


def env(name):
    value = os.environ.get(name)
    if not value:
        sys.exit(f"환경변수 {name} 가 설정되지 않았습니다.")
    return value


def get_json(url, headers):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def parse_count(value):
    # 검색광고 API는 10 미만을 "< 10" 문자열로 돌려준다
    if isinstance(value, str):
        return 5 if "<" in value else int(value.replace(",", ""))
    return int(value)


def fetch_search_volumes(keywords):
    """네이버 검색광고 키워드도구. 한 번에 힌트 키워드 5개까지, 공백 없이 보내야 한다."""
    api_key = env("NAVER_AD_API_KEY")
    secret = env("NAVER_AD_SECRET_KEY")
    customer = env("NAVER_AD_CUSTOMER_ID")
    path = "/keywordstool"
    volumes = {}
    for i in range(0, len(keywords), 5):
        batch = [k.replace(" ", "") for k in keywords[i:i + 5]]
        ts = str(int(time.time() * 1000))
        sig = base64.b64encode(
            hmac.new(secret.encode(), f"{ts}.GET.{path}".encode(), hashlib.sha256).digest()
        ).decode()
        query = urllib.parse.urlencode({"hintKeywords": ",".join(batch), "showDetail": 1})
        data = get_json(
            f"https://api.searchad.naver.com{path}?{query}",
            {"X-Timestamp": ts, "X-API-KEY": api_key, "X-Customer": customer, "X-Signature": sig},
        )
        for row in data.get("keywordList", []):
            rel = row["relKeyword"].replace(" ", "")
            if rel in batch:
                volumes[rel] = (parse_count(row["monthlyPcQcCnt"]), parse_count(row["monthlyMobileQcCnt"]))
        time.sleep(0.3)
    return volumes


def fetch_product_count(keyword):
    query = urllib.parse.urlencode({"query": keyword, "display": 1})
    data = get_json(
        f"https://openapi.naver.com/v1/search/shop.json?{query}",
        {"X-Naver-Client-Id": env("NAVER_CLIENT_ID"), "X-Naver-Client-Secret": env("NAVER_CLIENT_SECRET")},
    )
    return int(data.get("total", 0))


def main():
    volumes = fetch_search_volumes(KEYWORDS)
    rows = []
    for kw in KEYWORDS:
        pc, mobile = volumes.get(kw.replace(" ", ""), (0, 0))
        total = pc + mobile
        products = fetch_product_count(kw)
        ratio = round(products / total, 2) if total else None
        rows.append({"키워드": kw, "PC검색": pc, "모바일검색": mobile, "총검색": total,
                     "상품수": products, "경쟁강도": ratio})
        time.sleep(0.1)

    rows.sort(key=lambda r: (r["경쟁강도"] is None, r["경쟁강도"] or 0))
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"{'키워드':<16}{'총검색':>8}{'상품수':>10}{'경쟁강도':>10}")
    for r in rows:
        ratio = "-" if r["경쟁강도"] is None else r["경쟁강도"]
        print(f"{r['키워드']:<16}{r['총검색']:>8}{r['상품수']:>10}{ratio:>10}")
    print(f"\n저장: {os.path.abspath(OUT_PATH)}")


if __name__ == "__main__":
    main()
