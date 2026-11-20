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

def normalize(m, members):
    info = m["info"]
    side = {100: "blue", 200: "red"}
    teams = {"blue": [], "red": []}
    winner = None
    for p in info["participants"]:
        s = side[p["teamId"]]
        if p["win"]:
            winner = s
        teams[s].append({
            "name": members.get(p["puuid"]) or f'{p.get("riotIdGameName","?")}#{p.get("riotIdTagline","")}',
            "member": p["puuid"] in members,
            "champion": p["championName"],
            "k": p["kills"], "d": p["deaths"], "a": p["assists"],
        })
    return {
        "id": m["metadata"]["matchId"], "source": "riot", "queueId": info["queueId"],
        "date": info["gameStartTimestamp"], "duration": info["gameDuration"],
        "winner": winner, **teams,
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
    m = riot.match(mid)
    together = sum(p["puuid"] in members for p in m["info"]["participants"])
    if together >= MIN_TOGETHER:
        out.append(normalize(m, members))

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
        m = rso.match(pu, mid)
        if sum(p["puuid"] in optin for p in m["info"]["participants"]) >= MIN_TOGETHER:
            n = normalize(m, optin); n["source"] = "rso"  # 이름은 동의한 사람만
            # 동의 안 한 비멤버는 익명 처리 (정책: 커스텀 전적은 opt-in 한 본인만 공개)
            k = 0
            for s in ("blue", "red"):
                for p in n[s]:
                    if not p["member"]:
                        k += 1; p["name"] = f"익명 {k}"
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
