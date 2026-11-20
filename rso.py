"""RSO(Riot Sign On) 클라이언트 + lol-rso-match-v1 (표준 라이브러리만).

설정: ~/.riot/rso.json  {"client_id": "...", "client_secret": "...", "redirect_uri": "http://localhost:8787/callback"}
     Production 승인 후 Riot 이 발급한 RSO 클라이언트 값과, 등록한 redirect URI 를 넣는다.
토큰: ~/.riot/rso_tokens.json  {puuid: {riot_id, access_token, refresh_token, expires_at}}  (chmod 600)

주의(미검증): token 엔드포인트·client_secret_basic 방식은 Riot RSO 가이드(Google Docs) 기준 일반 OAuth2 형태로 구현.
승인 후 받는 가이드와 다르면 TOKEN_URL/인증 방식만 맞추면 된다.
"""
import base64, json, os, time, urllib.parse, urllib.request, urllib.error

AUTH = os.environ.get("RSO_AUTH", "https://auth.riotgames.com")
API = os.environ.get("RSO_API", "https://asia.api.riotgames.com")
CONF = os.path.expanduser(os.environ.get("RSO_CONF", "~/.riot/rso.json"))
TOKENS = os.path.expanduser(os.environ.get("RSO_TOKENS", "~/.riot/rso_tokens.json"))
UA = {"User-Agent": "naejeon-prototype/0.1"}

def conf():
    return json.load(open(CONF))

def configured():
    return os.path.exists(CONF)

def authorize_url(state):
    c = conf()
    return AUTH + "/authorize?" + urllib.parse.urlencode({
        "client_id": c["client_id"], "redirect_uri": c["redirect_uri"],
        "response_type": "code", "scope": "openid offline_access", "state": state})

def _token(form):
    c = conf()
    basic = base64.b64encode(f'{c["client_id"]}:{c["client_secret"]}'.encode()).decode()
    req = urllib.request.Request(AUTH + "/token", data=urllib.parse.urlencode(form).encode(),
                                 headers={**UA, "Authorization": "Basic " + basic,
                                          "Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=10) as r:
        t = json.load(r)
    t["expires_at"] = time.time() + int(t.get("expires_in", 3600)) - 60
    return t

def exchange_code(code):
    return _token({"grant_type": "authorization_code", "code": code, "redirect_uri": conf()["redirect_uri"]})

def _bearer_get(path, token, params=None):
    url = API + path + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(url, headers={**UA, "Authorization": "Bearer " + token})
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(int(e.headers.get("Retry-After", "5"))); continue
            raise
    raise RuntimeError("rate limited: " + path)

def me(token):
    return _bearer_get("/riot/account/v1/accounts/me", token)

# ---- 토큰 저장소 ----
def load_tokens():
    return json.load(open(TOKENS)) if os.path.exists(TOKENS) else {}

def save_tokens(ts):
    os.makedirs(os.path.dirname(TOKENS), exist_ok=True)
    fd = os.open(TOKENS, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(ts, f, indent=1)

def store_login(t):
    acct = me(t["access_token"])
    ts = load_tokens()
    ts[acct["puuid"]] = {"riot_id": f'{acct["gameName"]}#{acct["tagLine"]}', "opt_in": True,
                         "access_token": t["access_token"], "refresh_token": t.get("refresh_token"),
                         "expires_at": t["expires_at"]}
    save_tokens(ts)
    return ts[acct["puuid"]]["riot_id"]

def fresh_token(puuid):
    ts = load_tokens(); t = ts[puuid]
    if time.time() >= t["expires_at"]:
        if not t.get("refresh_token"):
            raise RuntimeError(f'{t["riot_id"]}: 토큰 만료, 다시 로그인 필요')
        n = _token({"grant_type": "refresh_token", "refresh_token": t["refresh_token"]})
        t.update(access_token=n["access_token"], expires_at=n["expires_at"],
                 refresh_token=n.get("refresh_token", t["refresh_token"]))
        save_tokens(ts)
    return t["access_token"]

# ---- lol-rso-match-v1 (Includes custom matches) ----
def custom_match_ids(puuid, count=20):
    return _bearer_get("/lol/rso-match/v1/matches/ids", fresh_token(puuid), {"queue": 0, "count": count})

def match(puuid, match_id):
    return _bearer_get(f"/lol/rso-match/v1/matches/{match_id}", fresh_token(puuid))

def timeline(puuid, match_id):
    return _bearer_get(f"/lol/rso-match/v1/matches/{match_id}/timeline", fresh_token(puuid))
