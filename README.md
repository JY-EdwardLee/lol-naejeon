# 내전 트래커 프로토타입

    python3 sync.py 20   # group.json 멤버들의 최근 20경기 수집 → data/matches.json
    python3 build.py     # → docs/stats.html

- group.json: 멤버 Riot ID 목록, min_together(같이 뛴 멤버 수 기준, 실사용은 2 이상)
- data/manual.json: RSO 전까지 내전 결과를 직접 입력
- 키: ~/.riot/key (dev key는 24시간마다 재발급)
- 다음 단계: RSO 승인 후 sync.py에 lol-rso-match-v1 소스 추가 (queue=0)

## RSO (Production 승인 후)
1. `~/.riot/rso.json` 에 Riot 이 발급한 값 입력:
   `{"client_id": "...", "client_secret": "...", "redirect_uri": "<등록한 redirect URI>"}`
2. `python3 login.py` → 각자 http://localhost:8787 접속해 Riot 로그인 (= 내전 전적 공유 동의). 토큰은 `~/.riot/rso_tokens.json`(600)에 저장.
3. `python3 sync.py 20` → 로그인한 사람 토큰으로 `lol-rso-match-v1`(queue=0) 내전 수집. 로그인 안 한 사람은 "익명 N" 으로 표시.
