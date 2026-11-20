"""Riot API 클라이언트 (표준 라이브러리만 사용). 키는 ~/.riot/key 에서 읽는다."""
import json, os, time, urllib.parse, urllib.request, urllib.error

KEY = open(os.path.expanduser("~/.riot/key")).read().strip()
REGION = "https://asia.api.riotgames.com"

def get(path, params=None, retries=3):
    url = REGION + path + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(url, headers={"X-Riot-Token": KEY, "User-Agent": "naejeon-prototype/0.1"})
    for _ in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:  # rate limit
                time.sleep(int(e.headers.get("Retry-After", "5")))
                continue
            raise
    raise RuntimeError("rate limited: " + path)

def puuid(game_name, tag):
    q = urllib.parse.quote
    return get(f"/riot/account/v1/accounts/by-riot-id/{q(game_name)}/{q(tag)}")["puuid"]

def match_ids(puuid, count=20, queue=None):
    p = {"count": count}
    if queue is not None:
        p["queue"] = queue
    return get(f"/lol/match/v5/matches/by-puuid/{puuid}/ids", p)

def match(match_id):
    return get(f"/lol/match/v5/matches/{match_id}")
