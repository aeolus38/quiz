#!/usr/bin/env python3
"""표지·지은이·출판사를 카카오 책 검색으로 미리 찾아 covers.json 에 저장한다.

covers.json 이 있으면 index.html 은 서버(api/book) 없이도 표지를 보여주므로
GitHub Pages 같은 정적 호스팅에서 그대로 동작한다.

books.json 을 바꾼 뒤 한 번 실행:
    set KAKAO_REST_API_KEY=발급받은_REST_키      (PowerShell: $env:KAKAO_REST_API_KEY="...")
    python tools/bake_covers.py
이미 찾은 책은 cover_cache.json 에서 바로 가져오므로 새 책만 조회한다.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import server  # noqa: E402  (kakao_lookup + cover_cache.json 재사용)

books = json.load(open(os.path.join(ROOT, "books.json"), encoding="utf-8"))
out, miss, err = {}, 0, 0
for i, b in enumerate(books, 1):
    title, pub = b.get("title", ""), b.get("publisher", "")
    r = server.kakao_lookup(title, pub, b.get("author", ""))
    if "error" in r:
        err += 1
        continue
    out[f"{title}|{pub}"] = r
    if not r.get("found"):
        miss += 1
    if i % 50 == 0:
        print(f"  {i}/{len(books)}")
with open(os.path.join(ROOT, "covers.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
print(f"covers.json: {len(out)}권 저장 (카카오에서 못 찾음 {miss}, 오류 {err})")
if err:
    print("오류가 있으면 KAKAO_REST_API_KEY 를 확인하고 다시 실행하세요.")
