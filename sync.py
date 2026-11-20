"""그룹 멤버들의 최근 경기를 모아 data/matches.json 에 정규화해 저장.

소스
- riot:   match-v5. 그룹 멤버가 2명 이상 함께 뛴 경기만 남김 (지금은 커스텀 게임 미포함)
- manual: data/manual.json 에 직접 입력한 내전 결과
- (예정) rso: lol-rso-match-v1, 로그인한 멤버 토큰으로 커스텀 게임 포함 조회
"""
import json, os, sys
import riot

HERE = os.path.dirname(os.path.abspath(__file__))
cfg = json.load(open(os.path.join(HERE, "group.json")))
COUNT = int(sys.argv[1]) if len(sys.argv) > 1 else 20
MIN_TOGETHER = cfg.get("min_together", 2)

WARD_LABEL = {"YELLOW_TRINKET": "노란 장신구", "CONTROL_WARD": "제어 와드", "SIGHT_WARD": "투명 와드",
              "BLUE_TRINKET": "파란 장신구", "UNDEFINED": "기타"}

def wards(tl, pid2):
    """타임라인 → [{t(초), ev: placed|killed, team, by, type}]. by = 설치자(placed) / 제거자(killed).
    WARD_KILL 은 어느 와드를 지웠는지·좌표가 API 에 없음."""
    out = []
    for f in tl["info"]["frames"]:
        for e in f["events"]:
            if e["type"] not in ("WARD_PLACED", "WARD_KILL"):
                continue
            pid = e.get("creatorId") if e["type"] == "WARD_PLACED" else e.get("killerId")
            if not pid or pid not in pid2:  # 0 = 미니언/기타
                continue
            if e.get("wardType", "UNDEFINED") == "UNDEFINED":  # 요릭 묘비·일라오이 촉수·니달리/진 덫 등 스킬 오브젝트
                continue
            team, name = pid2[pid]
            out.append({"t": e["timestamp"] // 1000, "ev": "placed" if e["type"] == "WARD_PLACED" else "killed",
                        "team": team, "by": name, "type": e.get("wardType", "UNDEFINED")})
    return out

def normalize(m, members, tl=None):
    info = m["info"]
    side = {100: "blue", 200: "red"}
    teams = {"blue": [], "red": []}
    winner = None
    pid2 = {}
    for p in info["participants"]:
        s = side[p["teamId"]]
        if p["win"]:
            winner = s
        teams[s].append({
            "name": members.get(p["puuid"]) or f'{p.get("riotIdGameName","?")}#{p.get("riotIdTagline","")}',
            "member": p["puuid"] in members,
            "champion": p["championName"],
            "k": p["kills"], "d": p["deaths"], "a": p["assists"],
            "vision": p.get("visionScore", 0), "wp": p.get("wardsPlaced", 0), "wk": p.get("wardsKilled", 0),
            "cw": p.get("detectorWardsPlaced", 0),
        })
        pid2[p.get("participantId")] = (s, teams[s][-1]["name"])
    return {
        "id": m["metadata"]["matchId"], "source": "riot", "queueId": info["queueId"],
        "date": info["gameStartTimestamp"], "duration": info["gameDuration"],
        "winner": winner, **teams,
        "wards": wards(tl, pid2) if tl else [],
    }

members = {}
for rid in cfg["members"]:
    name, tag = rid.split("#")
    members[riot.puuid(name, tag)] = rid
print(f"members: {len(members)}")

ids = set()
for pu in members:
    ids.update(riot.match_ids(pu, COUNT))
print(f"candidate matches: {len(ids)}")

out = []
for mid in sorted(ids, reverse=True):
    m = riot.cached("match", mid, riot.match)
    together = sum(p["puuid"] in members for p in m["info"]["participants"])
    if together >= MIN_TOGETHER:
        out.append(normalize(m, members, riot.cached("timeline", mid, riot.timeline)))

# ---- RSO: 로그인(동의)한 멤버 토큰으로 사용자 설정 게임 수집 ----
import rso
seen = {m["id"] for m in out}
tokens = rso.load_tokens()
optin = {pu: t["riot_id"] for pu, t in tokens.items() if t.get("opt_in")}
for pu in optin:
    try:
        cids = rso.custom_match_ids(pu, COUNT)
    except Exception as e:
        print(f'rso skip {optin[pu]}: {e}'); continue
    for mid in cids:
        if mid in seen:
            continue
        m = riot.cached("match", mid, lambda i: rso.match(pu, i))
        if sum(p["puuid"] in optin for p in m["info"]["participants"]) >= MIN_TOGETHER:
            tl = riot.cached("timeline", mid, lambda i: rso.timeline(pu, i))
            n = normalize(m, optin, tl); n["source"] = "rso"  # 이름은 동의한 사람만
            # 동의 안 한 비멤버는 익명 처리 (정책: 커스텀 전적은 opt-in 한 본인만 공개)
            k = 0; ren = {}
            for s in ("blue", "red"):
                for p in n[s]:
                    if not p["member"]:
                        k += 1; ren[p["name"]] = p["name"] = f"익명 {k}"
            for w in n["wards"]:
                w["by"] = ren.get(w["by"], w["by"])
            out.append(n); seen.add(mid)
if tokens:
    print(f"rso custom: {sum(m['source']=='rso' for m in out)} matches from {len(optin)} logged-in")

manual_path = os.path.join(HERE, "data", "manual.json")
if os.path.exists(manual_path):
    for m in json.load(open(manual_path)):
        m.setdefault("source", "manual")
        out.append(m)

json.dump(out, open(os.path.join(HERE, "data", "matches.json"), "w"), ensure_ascii=False, indent=1)
print(f"saved {len(out)} matches -> data/matches.json")
