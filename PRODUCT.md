# Production Key 신청서 초안 (developer.riotgames.com → Register Product)

> 포털 신청서는 영어로 작성. 아래 [ ] 는 채워야 할 부분.

## Product Name
Naejeon Tracker (내전 트래커)

## Product Description
Naejeon Tracker is a small, invite-only stats site for private friend groups in Korea
who regularly play custom 5v5 games ("내전") against each other.

Players sign in with Riot Sign On (RSO). For each signed-in player we read their own
match history through lol-rso-match-v1, including their custom matches, and show the
group a leaderboard (win rate, KDA, most-played champions), same-team pair win rates,
and a history of the group's custom games.

- Only players who have signed in with RSO and explicitly joined a group have their
  data shown, and only to members of that group. Nothing is public or indexed.
- Players can leave a group and delete their data at any time; we revoke and delete
  stored tokens on removal.
- We store only what is needed for the stats: match id, timestamp, teams, champion,
  K/D/A and result. No chat, no account info beyond Riot ID.
- No monetization, no ads, no betting. No features that give an in-game advantage.

## Why we need RSO
Custom matches are not returned by match-v5 for other players. lol-rso-match-v1
returns a player's own matches including custom games, which is the core of the
product. We do not request custom match data for any player who has not signed in.

## APIs used
- account-v1 (Riot ID → PUUID)
- match-v5 (regular matches played together, prototype)
- lol-rso-match-v1 /matches/ids, /matches/{matchId} (custom matches, after RSO approval)

## Expected traffic
[ ]개 그룹 × 10명 내외. 하루 1~2회 동기화. 수백 요청/일 수준.

## Prototype / URL
[배포 URL] — 현재 match-v5 + 수동 입력 기반 프로토타입 동작 중.

## Required pages (준비 필요)
- [ ] 공개 랜딩 페이지 (서비스 설명)
- [ ] Privacy Policy (수집 항목, 보관 기간, 삭제 방법)
- [ ] Terms of Service
- [ ] Riot 법적 고지 문구: "Naejeon Tracker isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games, and all associated properties are trademarks or registered trademarks of Riot Games, Inc."
