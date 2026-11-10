#!/usr/bin/env python3
"""독서퀴즈 서버 — 정적 파일 + 카카오 책 검색 프록시(표지·지은이·출판사 보강).

실행:
    export KAKAO_REST_API_KEY=xxxxxxxx   # 카카오 디벨로퍼스 REST API 키
    python3 server.py --port 8095

Caddy 예시 (하위 경로 /quiz/):
    handle_path /quiz/* {
        reverse_proxy localhost:8095
    }
페이지는 상대 경로만 쓰므로 어떤 하위 경로에 붙여도 동작한다.
"""
import argparse
import json
import os
import threading
import urllib.parse
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(ROOT, "cover_cache.json")
KAKAO_KEY = os.environ.get("KAKAO_REST_API_KEY", "")
_lock = threading.Lock()

try:
    with open(CACHE_FILE, encoding="utf-8") as f:
        CACHE = json.load(f)
except Exception:
    CACHE = {}


def _norm(s):
    return "".join(ch for ch in (s or "") if ch.isalnum()).lower()


def kakao_lookup(title, publisher="", author=""):
    key = f"{title}|{publisher}"
    with _lock:
        if key in CACHE:
            return CACHE[key]
    if not KAKAO_KEY:
        return {"error": "KAKAO_REST_API_KEY not set"}
    url = "https://dapi.kakao.com/v3/search/book?" + urllib.parse.urlencode(
        {"query": title, "target": "title", "size": 15}
    )
    req = urllib.request.Request(url, headers={"Authorization": f"KakaoAK {KAKAO_KEY}"})
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            docs = json.load(r).get("documents", [])
    except Exception as e:
        return {"error": str(e)}

    nt, npub, nauth = _norm(title), _norm(publisher), _norm(author)

    def score(d):
        s = 0
        dt = _norm(d.get("title"))
        if dt == nt:
            s += 10
        elif nt and (nt in dt or dt in nt):
            s += 5
        if npub and npub in _norm(d.get("publisher")):
            s += 4
        if nauth and any(_norm(a) and _norm(a) in nauth for a in d.get("authors", [])):
            s += 3
        if d.get("thumbnail"):
            s += 1
        return s

    best = max(docs, key=score) if docs else None
    if not best or score(best) < 5:
        result = {"found": False}
    else:
        result = {
            "found": True,
            "title": best.get("title", ""),
            "authors": best.get("authors", []),
            "translators": best.get("translators", []),
            "publisher": best.get("publisher", ""),
            "thumbnail": best.get("thumbnail", ""),
            "url": best.get("url", ""),
            "isbn": best.get("isbn", ""),
        }
    with _lock:
        CACHE[key] = result
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(CACHE, f, ensure_ascii=False)
        except Exception:
            pass
    return result


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.rstrip("/").endswith("/api/book") or parsed.path == "/api/book":
            q = urllib.parse.parse_qs(parsed.query)
            res = kakao_lookup(
                q.get("title", [""])[0], q.get("publisher", [""])[0], q.get("author", [""])[0]
            )
            body = json.dumps(res, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        return super().do_GET()

    def end_headers(self):
        if self.path.endswith(".json"):
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8095)
    ap.add_argument("--host", default="0.0.0.0")
    args = ap.parse_args()
    if not KAKAO_KEY:
        print("[경고] KAKAO_REST_API_KEY가 없어서 표지 자동 조회가 꺼져 있어요.")
    print(f"독서퀴즈 서버: http://{args.host}:{args.port}/")
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()
