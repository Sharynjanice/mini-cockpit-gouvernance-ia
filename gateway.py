"""Cœur de la passerelle : rôles, journal d'audit, budgets de tokens (stdlib uniquement)."""
import contextlib
import json
import os
import sqlite3
import sys
import time
import urllib.request

from tools import TOOLS

# Politique d'accès : quel rôle peut appeler quel outil.
POLICY = {
    "intern": {"read_calendar", "read_notes"},
    "manager": {"read_calendar", "read_notes", "send_email"},
    "admin": {"read_calendar", "read_notes", "send_email"},
}
DEFAULT_BUDGETS = {"projet-alpha": 20_000, "projet-beta": 3_000}


def connect() -> sqlite3.Connection:
    db = sqlite3.connect(os.environ.get("GATEWAY_DB", "gateway.db"))
    db.row_factory = sqlite3.Row
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS audit(ts REAL, role TEXT, project TEXT, tool TEXT,
                                         args TEXT, allowed INTEGER, reason TEXT);
        CREATE TABLE IF NOT EXISTS budgets(project TEXT PRIMARY KEY, limit_tokens INTEGER);
        CREATE TABLE IF NOT EXISTS usage(ts REAL, project TEXT, input_tokens INTEGER, output_tokens INTEGER);
        """
    )
    for project, limit in DEFAULT_BUDGETS.items():
        db.execute("INSERT OR IGNORE INTO budgets VALUES (?, ?)", (project, limit))
    db.commit()
    return db


@contextlib.contextmanager
def session():
    """Ouvre la base, valide les écritures puis ferme toujours la connexion."""
    db = connect()
    try:
        yield db
        db.commit()
    finally:
        db.close()


def used_tokens(project: str) -> int:
    with session() as db:
        row = db.execute(
            "SELECT COALESCE(SUM(input_tokens + output_tokens), 0) AS n FROM usage WHERE project = ?", (project,)
        ).fetchone()
    return row["n"]


def budget_status(project: str) -> dict:
    with session() as db:
        row = db.execute("SELECT limit_tokens FROM budgets WHERE project = ?", (project,)).fetchone()
    limit = row["limit_tokens"] if row else 0
    used = used_tokens(project)
    return {"project": project, "limit": limit, "used": used, "remaining": max(limit - used, 0)}


def record_usage(project: str, input_tokens: int, output_tokens: int) -> None:
    with session() as db:
        db.execute("INSERT INTO usage VALUES (?, ?, ?, ?)", (time.time(), project, input_tokens, output_tokens))


def check_budget(project: str) -> tuple[bool, str]:
    s = budget_status(project)
    if s["limit"] == 0:
        return False, f"projet inconnu ou sans budget : {project}"
    if s["remaining"] <= 0:
        return False, f"budget épuisé ({s['used']}/{s['limit']} tokens)"
    return True, "ok"


def check_access(role: str, tool: str) -> tuple[bool, str]:
    allowed = POLICY.get(role)
    if allowed is None:
        return False, f"rôle inconnu : {role}"
    if tool not in allowed:
        return False, f"le rôle « {role} » n'a pas le droit d'utiliser {tool}"
    return True, "ok"


def notify(event: dict) -> None:
    """Envoie un événement à n8n (webhook) si N8N_WEBHOOK_URL est défini. Ne bloque jamais l'appel."""
    url = os.environ.get("N8N_WEBHOOK_URL")
    if not url:
        print("[gateway] N8N_WEBHOOK_URL non défini : alerte non envoyée", file=sys.stderr)
        return
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(event).encode(),
            headers={"Content-Type": "application/json", "User-Agent": "mini-cockpit-ia/1.0"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            print(f"[gateway] alerte envoyée à n8n : HTTP {resp.status}", file=sys.stderr)
    except Exception as e:  # une panne de n8n ne doit pas casser la passerelle, mais on la signale
        print(f"[gateway] échec de l'alerte n8n ({url}) : {e!r}", file=sys.stderr)


def call(role: str, project: str, tool: str, **args) -> str:
    """Point d'entrée unique : contrôle le rôle, puis le budget, journalise, puis exécute."""
    ok, reason = check_access(role, tool)
    if ok:
        ok, reason = check_budget(project)
    if ok and tool not in TOOLS:
        ok, reason = False, f"outil inconnu : {tool}"
    with session() as db:
        db.execute(
            "INSERT INTO audit VALUES (?, ?, ?, ?, ?, ?, ?)",
            (time.time(), role, project, tool, json.dumps(args, ensure_ascii=False), int(ok), reason),
        )
    if not ok:
        notify({"event": "refused", "role": role, "project": project, "tool": tool, "reason": reason,
                "time": time.strftime("%Y-%m-%d %H:%M:%S")})
        return f"REFUSÉ : {reason}"
    return TOOLS[tool](**args)