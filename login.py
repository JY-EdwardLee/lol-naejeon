"""RSO 로그인 서버. 친구가 http://localhost:8787 접속 → Riot 로그인 → 토큰 저장(내전 공유 동의).
배포 시에는 같은 흐름을 HTTPS 도메인 + 등록한 redirect URI 로 띄운다."""
import html, http.server, os, secrets, urllib.parse
import rso

PORT = int(os.environ.get("PORT", "8787"))
states = set()

class H(http.server.BaseHTTPRequestHandler):
    def _send(self, code, body, loc=None):
        self.send_response(code)
        if loc: self.send_header("Location", loc)
        self.send_header("Content-Type", "text/html; charset=utf-8"); self.end_headers()
        self.wfile.write(body.encode())

    def do_GET(self):
        u = urllib.parse.urlparse(self.path); q = dict(urllib.parse.parse_qsl(u.query))
        if u.path == "/":
            return self._send(200, '<h2>내전 전적 공유</h2><p>로그인하면 내 사용자 설정 게임 전적을 '
                              '그룹에 공유하는 데 동의하게 됩니다.</p><a href="/login">Riot 계정으로 로그인</a>')
        if u.path == "/login":
            s = secrets.token_urlsafe(16); states.add(s)
            return self._send(302, "", rso.authorize_url(s))
        if u.path == "/callback":
            if q.get("state") not in states or "code" not in q:
                return self._send(400, "잘못된 요청 (state/code)")
            states.discard(q["state"])
            rid = rso.store_login(rso.exchange_code(q["code"]))
            return self._send(200, f"<p>{html.escape(rid)} 로그인 완료. 창을 닫아도 됩니다.</p>")
        self._send(404, "not found")

    def log_message(self, *a): pass

if __name__ == "__main__":
    if not rso.configured():
        raise SystemExit(f"{rso.CONF} 가 없습니다. Production 승인 후 RSO client_id/secret 을 넣으세요.")
    print(f"http://localhost:{PORT} 에서 로그인 대기"); http.server.HTTPServer(("", PORT), H).serve_forever()
