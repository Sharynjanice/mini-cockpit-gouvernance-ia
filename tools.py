"""Outils métier simulés (données de test). Aucun accès à de vraies boîtes mail."""

CALENDAR = {
    "2026-11-03": ["09:00 Point équipe", "14:00 Démo client Alpha"],
    "2026-11-04": ["10:30 Revue budget tokens"],
}
NOTES = {
    "conformite": "Checklist AI Act : registre des usages, information des salariés, revue des fournisseurs.",
    "onboarding": "Nouveau salarié : créer le compte IA, former (1h), activer la licence.",
}


def read_calendar(day: str) -> str:
    events = CALENDAR.get(day)
    return "\n".join(events) if events else f"Aucun événement le {day}."


def read_notes(topic: str) -> str:
    return NOTES.get(topic.lower(), f"Aucune note sur « {topic} ». Sujets : {', '.join(NOTES)}")


def send_email(to: str, subject: str, body: str) -> str:
    return f"[SIMULÉ] Email envoyé à {to} — objet : {subject}"


TOOLS = {"read_calendar": read_calendar, "read_notes": read_notes, "send_email": send_email}
