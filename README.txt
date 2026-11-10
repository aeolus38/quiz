브리스 독서퀴즈 — 설치 방법

1) 이 폴더를 서버에 복사 (예: ~/apps/reading-quiz)
2) 카카오 REST API 키 설정 후 실행 (책장 사이트와 같은 키 써도 됨)
     export KAKAO_REST_API_KEY=발급받은_REST_키
     python3 server.py --port 8095
3) Caddy에 하위 경로 추가 (공부 RPG /rpg/ 와 같은 방식)
     handle_path /quiz/* {
         reverse_proxy localhost:8095
     }
   → https://(ngrok 주소)/quiz/  로 접속

- 표지/지은이/출판사가 데이터에 없으면 카카오 책 검색으로 채우고 cover_cache.json 에 저장함
- 퀴즈 데이터는 books.json 하나. 업데이트할 때 이 파일만 바꾸면 됨
- 상태 표시: 내용 확인(출처로 줄거리 확인) / 검토 중(추정 섞임) / 퀴즈 준비 중
