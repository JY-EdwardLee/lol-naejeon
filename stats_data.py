"""data/matches.json + data/cache(원본 match/timeline) → 사이트용 압축 데이터.

공개 페이지용이므로 멤버(동의자)가 아닌 플레이어는 name=None 으로 내보내고 PUUID 는 절대 포함하지 않는다.
"""
import json, os, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "data", "cache")
QUEUE = {0: "내전", 400: "일반", 420: "솔로랭크", 430: "일반", 440: "자유랭크", 450: "칼바람", 490: "빠른대전",
         700: "격전", 710: "일반", 1700: "아레나", 1900: "URF"}

def ddragon():
    """Data Dragon 버전·챔피언 키 보정·아이템/스펠/룬 아이콘 매핑 (Riot 공식 공개 CDN)."""
    base = "https://ddragon.leagueoflegends.com"
    get = lambda u: json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "naejeon/0.1"}), timeout=10))
    try:
        v = get(base + "/api/versions.json")[0]
        ch = get(f"{base}/cdn/{v}/data/ko_KR/champion.json")["data"]
        sp = get(f"{base}/cdn/{v}/data/en_US/summoner.json")["data"]
        ru = get(f"{base}/cdn/{v}/data/ko_KR/runesReforged.json")
    except Exception as e:
        print("ddragon unavailable:", e); return {"v": None, "champ": {}, "byKey": {}, "spell": {}, "rune": {}}
    rune = {}
    for tree in ru:
        rune[tree["id"]] = {"n": tree["name"], "i": tree["icon"]}
        for slot in tree["slots"]:
            for r in slot["runes"]:
                rune[r["id"]] = {"n": r["name"], "i": r["icon"]}
    return {"v": v,
            "champ": {k.lower(): {"id": k, "n": c["name"]} for k, c in ch.items()},
            "byKey": {c["key"]: k for k, c in ch.items()},
            "spell": {int(s["key"]): s["id"] for s in sp.values()},
            "rune": rune}

def _load(mid, kind):
    p = os.path.join(CACHE, f"{mid}.{kind}.json")
    return json.load(open(p)) if os.path.exists(p) else None

def build(matches, public=None):
    """public: 이름을 공개해도 되는 Riot ID 집합(동의자). None 이면 모든 멤버 이름 표시(로컬 전용)."""
    show = (lambda n: n is not None and (public is None or n in public))
    dd = ddragon()
    ck = lambda n: dd["champ"].get((n or "").lower(), {"id": n, "n": n})
    out = []
    for nm in matches:
        raw, tl = _load(nm["id"], "match"), _load(nm["id"], "timeline")
        side_of = {}
        if not raw:  # 수동 입력 경기: 있는 것만
            ps = [{"name": p["name"] if p.get("member", True) and show(p["name"]) else None, "side": s, "champ": ck(p["champion"])["id"],
                   "champKo": ck(p["champion"])["n"], "k": p["k"], "d": p["d"], "a": p["a"]}
                  for s in ("blue", "red") for p in nm[s]]
            out.append({"id": nm["id"], "src": nm["source"], "q": 0, "qn": "내전", "date": nm["date"], "dur": nm.get("duration", 0),
                        "win": nm["winner"], "players": ps})
            continue
        info = raw["info"]; dur = max(info["gameDuration"], 1)
        norm = {"blue": iter(nm["blue"]), "red": iter(nm["red"])}
        ps = []
        for p in info["participants"]:
            s = "blue" if p["teamId"] == 100 else "red"
            n = next(norm[s]); ch = p.get("challenges", {})
            prim = p["perks"]["styles"][0]; sub = p["perks"]["styles"][1]
            ps.append({
                "name": n["name"] if n.get("member") and show(n["name"]) else None, "side": s, "pid": p["participantId"],
                "champ": ck(p["championName"])["id"], "champKo": ck(p["championName"])["n"],
                "pos": p.get("teamPosition") or p.get("individualPosition") or "",
                "k": p["kills"], "d": p["deaths"], "a": p["assists"], "lvl": p["champLevel"],
                "cs": p["totalMinionsKilled"] + p["neutralMinionsKilled"], "gold": p["goldEarned"],
                "dmg": p["totalDamageDealtToChampions"], "taken": p["totalDamageTaken"], "mitig": p["damageSelfMitigated"],
                "obj": p["damageDealtToObjectives"], "tur": p["damageDealtToTurrets"],
                "heal": p.get("totalHealsOnTeammates", 0), "shield": p.get("totalDamageShieldedOnTeammates", 0),
                "cc": p["timeCCingOthers"], "dead": p["totalTimeSpentDead"],
                "vision": p["visionScore"], "wp": p["wardsPlaced"], "wk": p["wardsKilled"], "cw": p["detectorWardsPlaced"],
                "kp": round(ch.get("killParticipation", 0), 3), "dshare": round(ch.get("teamDamagePercentage", 0), 3),
                "tshare": round(ch.get("damageTakenOnTeamPercentage", 0), 3), "solo": ch.get("soloKills", 0),
                "plates": ch.get("turretPlatesTaken", 0), "cs10": ch.get("laneMinionsFirst10Minutes", 0) + ch.get("jungleCsBefore10Minutes", 0),
                "skHit": ch.get("skillshotsHit", 0), "skDodge": ch.get("skillshotsDodged", 0),
                "fb": p["firstBloodKill"] or p["firstBloodAssist"], "ft": p["firstTowerKill"] or p["firstTowerAssist"],
                "multi": [p["doubleKills"], p["tripleKills"], p["quadraKills"], p["pentaKills"]],
                "spree": p["largestKillingSpree"], "steal": p.get("objectivesStolen", 0),
                "items": [p[f"item{i}"] for i in range(7)],
                "spells": [dd["spell"].get(p["summoner1Id"]), dd["spell"].get(p["summoner2Id"])],
                "rune": prim["selections"][0]["perk"], "rune2": sub["style"],
                "pings": sum(v for k, v in p.items() if k.endswith("Pings") and isinstance(v, int)),
                "_n": n["name"],
            })
            side_of[p["participantId"]] = len(ps) - 1
        teams = {}
        for t in info["teams"]:
            o = t["objectives"]
            teams["blue" if t["teamId"] == 100 else "red"] = {
                "first": {k: v["first"] for k, v in o.items()}, "kills": {k: v["kills"] for k, v in o.items()},
                "bans": [b["championId"] for b in t.get("bans", [])]}
        m = {"id": nm["id"], "src": nm["source"], "q": info["queueId"], "qn": QUEUE.get(info["queueId"], str(info["queueId"])),
             "date": info["gameStartTimestamp"], "dur": dur, "win": nm["winner"], "ver": ".".join(info["gameVersion"].split(".")[:2]),
             "players": ps, "teams": teams}
        if tl:
            fr = tl["info"]["frames"]
            idx = lambda pid: side_of.get(pid, -1)
            m["gold"] = [sum(f["participantFrames"][str(p["pid"])]["totalGold"] * (1 if p["side"] == "blue" else -1) for p in ps) for f in fr]
            # 분 단위 위치 · 골드 · CS · XP (플레이어 순서와 동일)
            # 동선은 멤버(동의자)만 — 용량 절약 + 비동의자 위치 비공개
            m["track"] = [[[f["participantFrames"][str(p["pid"])]["position"]["x"] // 10, f["participantFrames"][str(p["pid"])]["position"]["y"] // 10]
                           for f in fr] if p["name"] else None for p in ps]
            for i, p in enumerate(ps):
                pf = [f["participantFrames"][str(p["pid"])] for f in fr]
                p["g10"] = pf[10]["totalGold"] if len(pf) > 10 else None
                p["g15"] = pf[15]["totalGold"] if len(pf) > 15 else None
                p["x10"] = pf[10]["xp"] if len(pf) > 10 else None
                p["c15"] = pf[15]["minionsKilled"] + pf[15]["jungleMinionsKilled"] if len(pf) > 15 else None
            kills, objs = [], []
            for f in fr:
                for e in f["events"]:
                    t = e["timestamp"] // 1000
                    if e["type"] == "CHAMPION_KILL":
                        kills.append({"t": t, "x": e["position"]["x"] // 10, "y": e["position"]["y"] // 10,
                                      "k": idx(e.get("killerId")), "v": idx(e["victimId"]),
                                      "as": [idx(a) for a in e.get("assistingParticipantIds", [])]})
                    elif e["type"] == "ELITE_MONSTER_KILL":
                        side = "blue" if e.get("killerTeamId") == 100 else "red"
                        objs.append({"t": t, "type": e["monsterType"], "sub": e.get("monsterSubType"), "side": side, "by": idx(e.get("killerId"))})
                    elif e["type"] == "BUILDING_KILL":
                        side = "red" if e["teamId"] == 100 else "blue"  # teamId = 부서진 건물의 팀
                        objs.append({"t": t, "type": "TOWER" if e["buildingType"] == "TOWER_BUILDING" else "INHIBITOR",
                                     "sub": e.get("towerType") or e.get("laneType"), "side": side, "by": idx(e.get("killerId"))})
            m["kills"], m["objs"] = kills, objs
            who = {(p["side"], p["_n"]): i for i, p in enumerate(ps)}
            m["wards"] = [{"t": w["t"], "ev": w["ev"], "side": w["team"], "by": who.get((w["team"], w["by"]), -1), "type": w["type"]}
                          for w in nm.get("wards", [])]
        for p in ps: p.pop("_n", None)
        out.append(m)
    return {"dd": {"v": dd["v"], "byKey": dd["byKey"], "rune": {str(k): v for k, v in dd["rune"].items()}}, "matches": out}
