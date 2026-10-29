"""Démo budget : python chat_demo.py <role> <projet> "<question>"
Appelle l'API Claude avec les outils de la passerelle, mesure les tokens réels et bloque au dépassement."""
import os
import sys

import anthropic

import gateway

MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5")
TOOL_DEFS = [
    {"name": "read_calendar", "description": "Événements d'un jour (AAAA-MM-JJ).",
     "input_schema": {"type": "object", "properties": {"day": {"type": "string"}}, "required": ["day"]}},
    {"name": "read_notes", "description": "Lit une note interne (conformite, onboarding).",
     "input_schema": {"type": "object", "properties": {"topic": {"type": "string"}}, "required": ["topic"]}},
    {"name": "send_email", "description": "Envoie un email (simulé).",
     "input_schema": {"type": "object", "properties": {"to": {"type": "string"}, "subject": {"type": "string"},
                                                       "body": {"type": "string"}}, "required": ["to", "subject", "body"]}},
]


def main(role: str, project: str, question: str) -> None:
    client = anthropic.Anthropic()  # lit ANTHROPIC_API_KEY
    messages = [{"role": "user", "content": question}]
    for _ in range(5):  # garde-fou contre les boucles
        ok, reason = gateway.check_budget(project)
        if not ok:
            print(f"BLOQUÉ avant l'appel au modèle : {reason}")
            return
        resp = client.messages.create(model=MODEL, max_tokens=500, tools=TOOL_DEFS, messages=messages)
        gateway.record_usage(project, resp.usage.input_tokens, resp.usage.output_tokens)
        messages.append({"role": "assistant", "content": resp.content})
        results = [
            {"type": "tool_result", "tool_use_id": b.id, "content": gateway.call(role, project, b.name, **b.input)}
            for b in resp.content if b.type == "tool_use"
        ]
        if not results:
            print("".join(b.text for b in resp.content if b.type == "text"))
            print(gateway.budget_status(project))
            return
        messages.append({"role": "user", "content": results})


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
