Mini cockpit de gouvernance IA

Passerelle MCP qui encadre ce qu'un agent IA (Claude) a le droit de faire dans une entreprise : rôles et permissions, journal d'audit, budgets de tokens par projet et alertes automatiques via n8n.

Projet de démonstration réalisé pour comprendre les enjeux de gouvernance de l'IA générative en entreprise. Les outils (agenda, notes, email) sont simulés : aucun vrai mail n'est envoyé.

Démo

Avec le rôle intern, Claude peut lire l'agenda mais pas envoyer d'email. Le refus est journalisé et déclenche une alerte.

1. Le refus dans Claude	2. Le dashboard d'audit
Refus dans Claude	Dashboard
3. Journal dans Google Sheets	4. Alerte par e-mail
Google Sheets	E-mail d'alerte

Workflow n8n (exporté dans Alerte appel IA refusé.json) :

Workflow n8n

Fonctionnement
Claude (Desktop)
      │  appel d'un outil MCP
      ▼
server.py ──► gateway.call(rôle, projet, outil)
                 1. contrôle du rôle        (POLICY : intern / manager / admin)
                 2. contrôle du budget      (tokens consommés vs limite du projet)
                 3. journal d'audit         (SQLite : accepté ou refusé + raison)
                 4. exécution de l'outil    (tools.py, simulé)
                 5. si refus : webhook ──► n8n ──► Google Sheets + e-mail
dashboard.py ◄── lit la même base SQLite
Rôle	Agenda	Notes	Email
intern	oui	oui	refusé
manager	oui	oui	oui
admin	oui	oui	oui
Ce qui est démontré, et ce qui ne l'est pas
Démontré de bout en bout : contrôle des rôles, journal d'audit, dashboard, alerte n8n (captures ci-dessus).
Implémenté et couvert par les tests automatiques : blocage quand le budget de tokens d'un projet est épuisé (test_gateway.py).
Non démontré en situation réelle : la mesure de consommation avec l'API Claude (chat_demo.py), qui nécessite une clé API payante.
Installation (Windows, PowerShell)
powershell
python -m venv .venv
.venv\Scripts\activate
cd mini-cockpit-ia
pip install -r requirements.txt
python test_gateway.py      # 8 tests
python dashboard.py         # http://localhost:8000

requirements.txt fixe mcp<2 : la version 2 de la bibliothèque a renommé FastMCP.

Brancher à Claude Desktop

Dans claude_desktop_config.json (Paramètres, Développeur, Modifier la configuration) :

json
{
  "mcpServers": {
    "mini-cockpit": {
      "command": "C:/chemin/vers/.venv/Scripts/python.exe",
      "args": ["C:/chemin/vers/mini-cockpit-ia/server.py"],
      "env": {
        "GATEWAY_ROLE": "intern",
        "GATEWAY_PROJECT": "projet-alpha",
        "GATEWAY_DB": "C:/chemin/vers/mini-cockpit-ia/gateway.db",
        "N8N_WEBHOOK_URL": "https://VOTRE-INSTANCE.app.n8n.cloud/webhook/cockpit-refus"
      }
    }
  }
}

Quittez complètement Claude (icône de la barre des tâches, Quitter) puis rouvrez-le. N8N_WEBHOOK_URL est facultatif : sans lui, la passerelle fonctionne sans alertes.

Workflow n8n

Importez Alerte appel IA refusé.json, connectez vos comptes Google (Sheets, Gmail), créez une feuille avec les colonnes time, role, project, tool, reason, puis publiez le workflow et copiez l'URL de production du webhook.

Structure
Fichier	Rôle
gateway.py	Cœur : rôles, budgets, audit, alertes (bibliothèque standard uniquement)
server.py	Serveur MCP exposant les outils à Claude
tools.py	Outils simulés (agenda, notes, email)
dashboard.py	Tableau de bord web (budgets + journal)
chat_demo.py	Démo de mesure des tokens via l'API Claude
test_gateway.py	Tests automatiques
Alerte appel IA refusé.json	Workflow n8n d'alerte exporté
01-…05-*.PNG	Captures d'écran de la démo
Limites connues et pistes d'évolution
Identité : le rôle vient d'une variable d'environnement. En production : OAuth et un jeton par utilisateur.
Budget : vérifié avant chaque appel ; un appel peut dépasser la limite avant d'être comptabilisé.
Stockage : SQLite local. En production : base partagée, multi-client, durée de conservation des logs.
Webhook : l'URL n8n n'est pas authentifiée ; il faudrait un secret partagé.
Hors périmètre : détection du shadow IA, documents de conformité, suivi des licences.
Auteure

Sharyn Janice Djiodop Foka · LinkedIn · GitHub · Portfolio
