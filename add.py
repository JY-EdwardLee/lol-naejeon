"""내전 결과 한 판을 대화식으로 입력 → data/manual.json 에 추가하고 사이트 재생성.

선수 한 줄 형식:  이름 챔피언 K/D/A     (예: 라민 yml 아리 7/3/9)
- 이름은 group.json 멤버면 태그(#...) 생략 가능. 띄어쓰기 있어도 됨.
- K/D/A 모르면 생략 가능. 빈 줄 입력하면 그 팀 입력 끝.
"""
import json, os, subprocess, sys, time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
cfg = json.load(open(os.path.join(HERE, "group.json")))
by_short = {m.split("#")[0].lower(): m for m in cfg["members"]}

def resolve(name):
    key = name.split("#")[0].lower().replace(" ", "")
    hits = [m for s, m in by_short.items() if s.replace(" ", "") == key]
    hits = hits or [m for s, m in by_short.items() if s.replace(" ", "").startswith(key)]
    return (hits[0], True) if len(hits) == 1 else (name, False)

def parse(line):
    t = line.split()
    k = d = a = 0
    if "/" in t[-1]:
        k, d, a = (int(x) for x in t.pop().split("/"))
    champ = t.pop() if len(t) > 1 else "?"
    name, member = resolve(" ".join(t))
    return {"name": name, "member": member, "champion": champ, "k": k, "d": d, "a": a}

def team(label):
    print(f"\n[{label}] 선수 입력 (빈 줄로 끝)")
    ps = []
    while len(ps) < 5:
        line = input(f"  {len(ps)+1}> ").strip()
        if not line:
            break
        ps.append(parse(line))
        p = ps[-1]
        print(f"     → {p['name']}{' (멤버)' if p['member'] else ''} / {p['champion']} / {p['k']}/{p['d']}/{p['a']}")
    return ps

d = input("날짜 (YYYY-MM-DD HH:MM, 엔터=지금): ").strip()
ts = int((datetime.strptime(d, "%Y-%m-%d %H:%M").timestamp() if d else time.time()) * 1000)
blue, red = team("블루"), team("레드")
w = ""
while w not in ("b", "r"):
    w = input("\n이긴 팀? (b=블루 / r=레드): ").strip().lower()
mins = input("게임 시간(분, 엔터=생략): ").strip()

path = os.path.join(HERE, "data", "manual.json")
manual = json.load(open(path)) if os.path.exists(path) else []
manual = [m for m in manual if not m["id"].startswith("manual-sample")]  # 샘플 제거
manual.append({"id": f"manual-{ts}", "source": "manual", "date": ts,
               "duration": int(mins) * 60 if mins else 0,
               "winner": "blue" if w == "b" else "red", "blue": blue, "red": red})
json.dump(manual, open(path, "w"), ensure_ascii=False, indent=1)

# API 다시 안 부르고 matches.json 의 수동 경기만 교체
mp = os.path.join(HERE, "data", "matches.json")
ms = [m for m in (json.load(open(mp)) if os.path.exists(mp) else []) if m.get("source") != "manual"]
json.dump(ms + manual, open(mp, "w"), ensure_ascii=False, indent=1)
print(f"\n저장 완료 (수동 내전 {len(manual)}판)")
subprocess.run([sys.executable, os.path.join(HERE, "build.py")])
