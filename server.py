"""Serveur MCP : expose les outils à Claude, chaque appel passe par la passerelle."""
import os

from mcp.server.fastmcp import FastMCP

import gateway

mcp = FastMCP("mini-cockpit-ia")


def identity() -> tuple[str, str]:
    # Limite connue : en stdio, l'identité vient de variables d'environnement
    # (une vraie passerelle utiliserait OAuth / un jeton par utilisateur).
    return os.environ.get("GATEWAY_ROLE", "intern"), os.environ.get("GATEWAY_PROJECT", "projet-alpha")


@mcp.tool()
def read_calendar(day: str) -> str:
    """Liste les événements d'un jour (format AAAA-MM-JJ)."""
    return gateway.call(*identity(), "read_calendar", day=day)


@mcp.tool()
def read_notes(topic: str) -> str:
    """Lit une note interne (ex. conformite, onboarding)."""
    return gateway.call(*identity(), "read_notes", topic=topic)


@mcp.tool()
def send_email(to: str, subject: str, body: str) -> str:
    """Envoie un email (simulé). Réservé aux rôles manager et admin."""
    return gateway.call(*identity(), "send_email", to=to, subject=subject, body=body)


if __name__ == "__main__":
    mcp.run()
