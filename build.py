"""data/matches.json -> docs/ (GitHub Pages): index(소개) · stats(전적) · privacy · terms.
공개 페이지이므로 그룹 멤버(동의자)가 아닌 플레이어 이름은 표시하지 않는다."""
import json, os, html, datetime
from collections import defaultdict
from itertools import combinations

HERE = os.path.dirname(os.path.abspath(__file__))
matches = json.load(open(os.path.join(HERE, "data", "matches.json")))
title = json.load(open(os.path.join(HERE, "group.json"))).get("title", "내전 전적")

ps = defaultdict(lambda: {"g": 0, "w": 0, "k": 0, "d": 0, "a": 0, "champ": defaultdict(int)})
duo = defaultdict(lambda: [0, 0])
for m in matches:
    for s in ("blue", "red"):
        won = m["winner"] == s
        mem = [p for p in m[s] if p.get("member", True)]
        for p in mem:
            x = ps[p["name"]]
            x["g"] += 1; x["w"] += won
            x["k"] += p["k"]; x["d"] += p["d"]; x["a"] += p["a"]
            x["champ"][p["champion"]] += 1
        for a, b in combinations(sorted(p["name"] for p in mem), 2):
            duo[(a, b)][0] += 1; duo[(a, b)][1] += won

e = html.escape
pct = lambda w, g: f"{100*w/g:.0f}%" if g else "-"
rows = "".join(
    f"<tr><td>{e(n)}</td><td>{x['g']}</td><td>{x['w']}-{x['g']-x['w']}</td><td>{pct(x['w'],x['g'])}</td>"
    f"<td>{(x['k']+x['a'])/max(x['d'],1):.2f}</td>"
    f"<td>{e(', '.join(c for c,_ in sorted(x['champ'].items(), key=lambda t:-t[1])[:3]))}</td></tr>"
    for n, x in sorted(ps.items(), key=lambda t: (-t[1]['w']/t[1]['g'], -t[1]['g'])))
duos = "".join(
    f"<tr><td>{e(a)} + {e(b)}</td><td>{g}</td><td>{pct(w,g)}</td></tr>"
    for (a, b), (g, w) in sorted(duo.items(), key=lambda t: (-t[1][0], -t[1][1])))
def pname(p):
    return f"<b>{e(p['name'])}</b>" if p.get("member", True) else "<span class=anon>플레이어</span>"
def team(m, s):
    return "<br>".join(f"{pname(p)} · {e(p['champion'])} {p['k']}/{p['d']}/{p['a']}" for p in m[s])
recent = "".join(
    f"<tr><td>{datetime.datetime.fromtimestamp(m['date']/1000):%m-%d %H:%M}<br><small>{e(m['source'])}</small></td>"
    f"<td class='{'win' if m['winner']=='blue' else ''}'>{team(m,'blue')}</td>"
    f"<td class='{'win' if m['winner']=='red' else ''}'>{team(m,'red')}</td></tr>"
    for m in sorted(matches, key=lambda m: -m["date"])[:30])

APP = "Naejeon Tracker"
NAV = '<nav><a href="index.html">소개</a> · <a href="stats.html">전적</a> · <a href="privacy.html">개인정보처리방침</a> · <a href="terms.html">이용약관</a></nav>'
FOOT = (f"<footer><p>{APP} isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games "
        "or anyone officially involved in producing or managing Riot Games properties. Riot Games, and all associated "
        "properties are trademarks or registered trademarks of Riot Games, Inc.</p></footer>")
CSS = """:root{--bg:#fff;--fg:#1a1a1a;--mute:#666;--line:#e5e5e5;--win:#e8f3ff;--acc:#2563eb}
@media (prefers-color-scheme:dark){:root{--bg:#141414;--fg:#eee;--mute:#999;--line:#2a2a2a;--win:#14283d;--acc:#60a5fa}}
body{background:var(--bg);color:var(--fg);font:14px/1.6 -apple-system,sans-serif;max-width:900px;margin:0 auto;padding:16px}
a{color:var(--acc)}nav{margin-bottom:16px}footer{margin-top:40px;border-top:1px solid var(--line);color:var(--mute);font-size:12px}
table{border-collapse:collapse;width:100%;margin:8px 0 24px}td,th{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
th{color:var(--mute);font-weight:500}.win{background:var(--win)}small,.anon{color:var(--mute)}.wrap{overflow-x:auto}
.btn{display:inline-block;padding:10px 16px;border-radius:8px;background:var(--acc);color:#fff;text-decoration:none}"""
def shell(t, body):
    return (f'<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>{e(t)}</title><style>{CSS}</style>{NAV}{body}{FOOT}</html>")
CONTACT = json.load(open(os.path.join(HERE, "group.json"))).get("contact", "[연락처]")
TODAY = f"{datetime.date.today():%Y-%m-%d}"

stats = f"""<h1>{e(title)}</h1><p><small>경기 {len(matches)}건 · 갱신 {datetime.datetime.now():%Y-%m-%d %H:%M}</small></p>
<h2>멤버 순위</h2><div class=wrap><table><tr><th>멤버</th><th>판수</th><th>전적</th><th>승률</th><th>KDA</th><th>모스트</th></tr>{rows}</table></div>
<h2>같은 팀 조합</h2><div class=wrap><table><tr><th>조합</th><th>판수</th><th>승률</th></tr>{duos or '<tr><td colspan=3>데이터 없음</td></tr>'}</table></div>
<h2>최근 경기</h2><div class=wrap><table><tr><th>일시</th><th>블루</th><th>레드</th></tr>{recent}</table></div>"""

landing = f"""<h1>{APP}</h1>
<p><b>친구들끼리 하는 롤 내전(사용자 설정 게임) 전적과 승률을 자동으로 정리해 주는 서비스입니다.</b><br>
<small>A stats tracker for League of Legends custom games played within a private group of friends.</small></p>
<h2>어떻게 동작하나요</h2><ol>
<li>그룹 멤버가 <b>Riot 계정으로 로그인(RSO)</b>해 자신의 사용자 설정 게임 전적 공유에 동의합니다.</li>
<li>동의한 멤버의 내전 기록을 Riot API(<code>lol-rso-match-v1</code>)로 가져옵니다.</li>
<li>멤버별 승률·KDA·모스트 챔피언, 같은 팀 조합 승률, 최근 경기를 보여줍니다.</li></ol>
<p>로그인(동의)하지 않은 플레이어의 이름과 개인 전적은 표시하지 않습니다. 동의는 언제든 철회할 수 있습니다.</p>
<p><a class=btn href="stats.html">전적 보기 (데모)</a> &nbsp; <span class=anon>Riot 계정 로그인: 준비 중</span></p>
<h2>How it works (EN)</h2><ul>
<li>Members sign in with Riot Sign On and opt in to sharing their custom match history with their group.</li>
<li>We fetch opted-in members' custom matches via <code>lol-rso-match-v1</code> and show win rates, KDA, champion picks and duo win rates.</li>
<li>Players who have not opted in are never shown by name. No MMR/ELO or skill rating is calculated.</li></ul>"""

privacy = f"""<h1>개인정보처리방침 / Privacy Policy</h1><p><small>시행일 {TODAY}</small></p>
<h2>1. 수집하는 정보</h2><ul>
<li>Riot 로그인(RSO) 시: Riot ID(게임 이름#태그), PUUID, Riot이 발급한 액세스·리프레시 토큰</li>
<li>Riot API로 조회한 경기 정보: 챔피언, 킬/데스/어시스트, 승패, 경기 시각</li></ul>
<p>이메일, 비밀번호, 결제 정보는 수집하지 않습니다. 비밀번호는 Riot이 직접 처리하며 본 서비스에 전달되지 않습니다.</p>
<h2>2. 이용 목적</h2><p>그룹 멤버의 내전 전적·승률 통계를 만들어 그룹에 보여주는 데에만 사용합니다. 광고·판매·제3자 제공은 하지 않습니다.</p>
<h2>3. 공개 범위</h2><p>통계에는 로그인해 공유에 동의한 멤버만 이름이 표시됩니다. 동의하지 않은 플레이어는 이름 없이 표시됩니다.</p>
<h2>4. 보관 및 삭제</h2><p>토큰은 접근이 제한된 저장소에 보관합니다. 동의 철회 또는 삭제 요청 시 토큰과 해당 플레이어의 통계를 지체 없이 삭제합니다.
Riot 계정 설정에서 앱 연결을 해제해도 토큰은 더 이상 사용할 수 없습니다.</p>
<h2>5. 문의</h2><p>{e(CONTACT)}</p>
<h2>English summary</h2><p>We collect your Riot ID, PUUID and RSO tokens when you sign in, and match data (champion, K/D/A, result, time)
from the Riot API. Data is used only to show stats to your group. We never sell or share it. Players who have not opted in are not shown by name.
You can revoke consent and request deletion at any time via the contact above.</p>"""

terms = f"""<h1>이용약관 / Terms of Service</h1><p><small>시행일 {TODAY}</small></p><ol>
<li>본 서비스는 개인이 운영하는 비상업적 팬 프로젝트이며 Riot Games와 무관합니다.</li>
<li>이용자는 Riot 로그인으로 자신의 사용자 설정 게임 전적을 그룹에 공유하는 데 동의하며, 언제든 철회할 수 있습니다.</li>
<li>통계는 Riot API 데이터를 바탕으로 하며 정확성·가용성을 보장하지 않습니다. Riot API 정책 변경에 따라 기능이 바뀌거나 중단될 수 있습니다.</li>
<li>본 서비스는 공식 랭크를 대체하는 MMR/ELO 등 실력 점수를 제공하지 않습니다.</li>
<li>다른 플레이어를 괴롭히거나 비방할 목적으로 이용할 수 없습니다.</li>
<li>문의: {e(CONTACT)}</li></ol>
<p><small>This is a free, non-commercial fan project. By signing in you agree to share your custom match history with your group; you may revoke this at any time.
Stats are provided as-is. Not endorsed by Riot Games.</small></p>"""

out = os.path.join(HERE, "docs")
os.makedirs(out, exist_ok=True)
for fn, t, b in [("index.html", APP, landing), ("stats.html", title, stats), ("privacy.html", "개인정보처리방침", privacy), ("terms.html", "이용약관", terms)]:
    open(os.path.join(out, fn), "w").write(shell(t, b))
print(f"docs/ ({len(ps)} members, {len(matches)} matches)")
