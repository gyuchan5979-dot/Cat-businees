"""네이버 자동완성으로 연관 키워드 수집 (API 키 불필요).

자동완성은 검색량이 많은 순서로 노출되므로, 키 없이도 수요가 있는 키워드를 넓게 찾을 수 있다.
실행: python3 scripts/autocomplete_keywords.py  → data/autocomplete_keywords.csv
"""
import csv
import json
import os
import time
import urllib.parse
import urllib.request

from keyword_competition import KEYWORDS

SEEDS = ["노령묘", "노묘", "노령묘 용품", "노묘 용품", "나이든 고양이", "고양이 관절", "고양이 노화"]

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "autocomplete_keywords.csv")


def autocomplete(query):
    url = "https://ac.search.naver.com/nx/ac?" + urllib.parse.urlencode(
        {"q": query, "st": 100, "r_format": "json"})
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return [item[0] for item in data["items"][0]] if data.get("items") else []


def main():
    rows = []
    for query in SEEDS + KEYWORDS:
        for rank, suggestion in enumerate(autocomplete(query), start=1):
            rows.append({"입력": query, "순위": rank, "자동완성": suggestion})
        time.sleep(0.2)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["입력", "순위", "자동완성"])
        writer.writeheader()
        writer.writerows(rows)

    for query in SEEDS + KEYWORDS:
        found = [r["자동완성"] for r in rows if r["입력"] == query]
        print(f"[{query}] " + (", ".join(found) if found else "(자동완성 없음)"))
    print(f"\n저장: {os.path.abspath(OUT_PATH)}")


if __name__ == "__main__":
    main()
