"""Tableau de bord : python dashboard.py puis http://localhost:8000 (stdlib uniquement)."""
import html
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import gateway


def render() -> str:
    with gateway.session() as db:
        projects = [r["project"] for r in db.execute("SELECT project FROM budgets ORDER BY project")]
        logs = db.execute("SELECT * FROM audit ORDER BY ts DESC LIMIT 50").fetchall()
        refused = db.execute("SELECT COUNT(*) AS n FROM audit WHERE allowed = 0").fetchone()["n"]
    cards = ""
    for p in projects:
        s = gateway.budget_status(p)
        pct = min(100, round(100 * s["used"] / s["limit"])) if s["limit"] else 0
        color = "#c0392b" if pct >= 100 else "#e67e22" if pct >= 80 else "#27ae60"
        cards += (f"<div class='c'><b>{html.escape(p)}</b><br>{s['used']} / {s['limit']} tokens"
                  f"<div class='bar'><div style='width:{pct}%;background:{color}'></div></div></div>")
    rows = "".join(
        f"<tr class='{'' if r['allowed'] else 'no'}'><td>{time.strftime('%H:%M:%S', time.localtime(r['ts']))}</td>"
        f"<td>{html.escape(r['role'])}</td><td>{html.escape(r['project'])}</td><td>{html.escape(r['tool'])}</td>"
        f"<td>{'accepté' if r['allowed'] else 'REFUSÉ'}</td><td>{html.escape(r['reason'])}</td></tr>"
        for r in logs
    )
    return f"""<!doctype html><meta charset=utf-8><meta http-equiv=refresh content=3>
<title>Mini cockpit IA</title><style>
body{{font:14px system-ui;margin:2rem;max-width:960px}} .c{{display:inline-block;margin:0 1rem 1rem 0;padding:1rem;border:1px solid #ccc;border-radius:8px;min-width:240px}}
.bar{{height:8px;background:#eee;border-radius:4px;margin-top:6px}} .bar div{{height:8px;border-radius:4px}}
table{{border-collapse:collapse;width:100%}} td,th{{padding:6px;border-bottom:1px solid #eee;text-align:left}} .no{{background:#fdecea}}
</style><h1>Mini cockpit de gouvernance IA</h1><h2>Budgets par projet</h2>{cards}
<h2>Journal d'audit ({refused} appels refusés)</h2>
<table><tr><th>Heure</th><th>Rôle</th><th>Projet</th><th>Outil</th><th>Résultat</th><th>Raison</th></tr>{rows}</table>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = render().encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    print("Dashboard sur http://localhost:8000")
    HTTPServer(("127.0.0.1", 8000), Handler).serve_forever()