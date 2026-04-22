from flask import Flask, request
import urllib.request, urllib.error, json, os, threading, base64, ssl
from datetime import datetime

app = Flask(__name__)

TOKEN = "8710994922:AAG_tiyBXu0Q_KS7Ck8UKmkPR6xXbmskai8"
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

SYSTEM_PROMPT = """Tu es l'assistant IA de Dikenga Design, UI/UX Designer freelance à Paris. Tu as accès à des outils pour accomplir de vraies tâches.

CONTEXTE COMPLET :
- Site : dikengadesign.fr → repo GitHub Bihem/bihem.github.io
- Email : dikengadesign@gmail.com | Tel : +33 7 67 53 70 59
- Malt : malt.fr/profile/mesrevesbouzanga1 | LinkedIn : linkedin.com/in/dikengadesign/
- TJM : ~445€/j | Mission urgente : Senior UX/UI Saint-Denis 600€/j avant 1er mai
- Stack : HTML/CSS/JS statique, Figma, Design Systems, accessibilité
- Telegram bot token : 8710994922:AAG_tiyBXu0Q_KS7Ck8UKmkPR6xXbmskai8
- Chat ID : 6743914052
- GMB : 3 avis Google, fiche revendiquée

OUTILS DISPONIBLES :
- github_get_file : lire un fichier du site
- github_push_file : publier/modifier un fichier sur dikengadesign.fr
- web_fetch : récupérer une page web (recherche de missions, etc.)
- send_progress : envoyer un message intermédiaire sur Telegram

INSTRUCTIONS :
- Quand l'utilisateur demande de publier un article, chercher des missions, modifier le site → utilise les outils pour le faire vraiment
- Pour les articles de blog, les ajouter dans blog.html (repo Bihem/bihem.github.io)
- Réponds en français, concis et actionnable
- Pour les tâches longues, utilise send_progress pour tenir informé"""

TOOLS = [
    {
        "name": "github_get_file",
        "description": "Lire le contenu d'un fichier dans le repo GitHub Bihem/*",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Nom du repo ex: bihem.github.io"},
                "path": {"type": "string", "description": "Chemin du fichier ex: blog.html"}
            },
            "required": ["repo", "path"]
        }
    },
    {
        "name": "github_push_file",
        "description": "Créer ou mettre à jour un fichier dans le repo GitHub Bihem/*",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Nom du repo ex: bihem.github.io"},
                "path": {"type": "string", "description": "Chemin du fichier ex: blog.html"},
                "content": {"type": "string", "description": "Contenu complet du fichier"},
                "message": {"type": "string", "description": "Message de commit"}
            },
            "required": ["repo", "path", "content", "message"]
        }
    },
    {
        "name": "web_fetch",
        "description": "Récupérer le contenu HTML d'une URL (missions freelance, actualités, etc.)",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL complète à récupérer"},
                "max_chars": {"type": "integer", "description": "Nombre max de caractères à retourner (défaut 4000)"}
            },
            "required": ["url"]
        }
    },
    {
        "name": "send_progress",
        "description": "Envoyer un message de progression sur Telegram pendant l'exécution d'une tâche longue",
        "input_schema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Message de progression à envoyer"}
            },
            "required": ["message"]
        }
    }
]

conversation_history = {}

def send(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    # Truncate if too long for Telegram (4096 char limit)
    if len(text) > 4000:
        text = text[:3990] + "\n...[tronqué]"
    data = json.dumps({"chat_id": str(chat_id), "text": text}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, context=ctx) as r:
            return json.loads(r.read())
    except Exception as e:
        print("Erreur send:", e)

def gh_api(path, method="GET", data=None):
    url = f"https://api.github.com{path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    req = urllib.request.Request(url, headers=headers, method=method)
    if data:
        req.data = json.dumps(data).encode()
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx) as r:
        return json.loads(r.read())

def execute_tool(tool_name, tool_input, chat_id):
    try:
        if tool_name == "send_progress":
            send(chat_id, "⏳ " + tool_input["message"])
            return {"ok": True}

        elif tool_name == "github_get_file":
            repo = tool_input["repo"]
            path = tool_input["path"]
            result = gh_api(f"/repos/Bihem/{repo}/contents/{path}")
            content = base64.b64decode(result["content"]).decode("utf-8")
            sha = result["sha"]
            return {"content": content[:6000], "sha": sha, "size": len(content)}

        elif tool_name == "github_push_file":
            repo = tool_input["repo"]
            path = tool_input["path"]
            content = tool_input["content"]
            message = tool_input["message"]
            # Get current SHA
            try:
                info = gh_api(f"/repos/Bihem/{repo}/contents/{path}")
                sha = info["sha"]
            except:
                sha = None
            payload = {
                "message": message,
                "content": base64.b64encode(content.encode("utf-8")).decode()
            }
            if sha:
                payload["sha"] = sha
            result = gh_api(f"/repos/Bihem/{repo}/contents/{path}", "PUT", payload)
            return {"ok": True, "commit": result["commit"]["sha"][:7], "url": f"https://dikengadesign.fr/{path}"}

        elif tool_name == "web_fetch":
            url = tool_input["url"]
            max_chars = tool_input.get("max_chars", 4000)
            headers = {"User-Agent": "Mozilla/5.0 (compatible; DikengaBot/1.0)"}
            req = urllib.request.Request(url, headers=headers)
            ctx = ssl.create_default_context()
            try:
                with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
                    raw = r.read().decode("utf-8", errors="ignore")
                    # Strip HTML tags roughly
                    import re
                    clean = re.sub(r'<[^>]+>', ' ', raw)
                    clean = re.sub(r'\s+', ' ', clean).strip()
                    return {"content": clean[:max_chars]}
            except Exception as e:
                return {"error": str(e)}

    except Exception as e:
        return {"error": str(e)}

def run_agent(chat_id, user_message):
    history = conversation_history.get(chat_id, [])
    history.append({"role": "user", "content": user_message})

    messages = history[-10:]  # keep last 10 turns

    for iteration in range(6):
        payload = {
            "model": "claude-sonnet-4-6",
            "max_tokens": 1500,
            "system": SYSTEM_PROMPT,
            "tools": TOOLS,
            "messages": messages
        }
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=data,
            headers={
                "Content-Type": "application/json",
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01"
            }
        )
        try:
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, context=ctx, timeout=55) as r:
                response = json.loads(r.read())
        except Exception as e:
            send(chat_id, f"⚠️ Erreur API Claude : {e}")
            return

        stop_reason = response.get("stop_reason")
        content = response.get("content", [])

        if stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": content})
            tool_results = []
            for block in content:
                if block["type"] == "tool_use":
                    result = execute_tool(block["name"], block["input"], chat_id)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block["id"],
                        "content": json.dumps(result, ensure_ascii=False)
                    })
            messages.append({"role": "user", "content": tool_results})

        else:
            # Final response
            final_text = ""
            for block in content:
                if block.get("type") == "text":
                    final_text += block["text"]
            if final_text:
                send(chat_id, final_text)
            # Update history
            history.append({"role": "assistant", "content": final_text})
            conversation_history[chat_id] = history[-12:]
            return

    send(chat_id, "⚠️ Tâche interrompue après 6 itérations.")

@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json(silent=True)
    if not data or "message" not in data:
        return "OK", 200

    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "").strip()

    if text.startswith("/start"):
        send(chat_id, "👋 Bonjour ! Je suis l'assistant IA de Dikenga Design.\n\nJe peux accomplir de vraies tâches :\n→ Publier un article sur le blog\n→ Chercher des missions freelance\n→ Modifier le site dikengadesign.fr\n→ Rédiger des messages clients\n\nEnvoie-moi une instruction en français.\n\nCommandes rapides :\n/rapport — Rapport express\n/status — Statut agents\n/missions — Missions détectées\n/reset — Nouvelle conversation\n/help — Aide")

    elif text.startswith("/rapport"):
        now = datetime.now().strftime("%H:%M %d/%m")
        send(chat_id, f"📊 RAPPORT EXPRESS — {now}\n\n✅ dikengadesign.fr — En ligne\n✅ 9 agents actifs\n✅ Email + Telegram opérationnels\n✅ GMB : 3 avis Google\n\n💼 Mission prioritaire :\n→ Senior UX/UI Saint-Denis 600€/j\n→ Démarrage avant 1er mai\n\n⏰ Prochain rapport complet dans 3h")

    elif text.startswith("/status"):
        send(chat_id, "🤖 AGENTS ACTIFS\n\n✅ Rapport 3h (Telegram + Email)\n✅ Blog SEO quotidien 8h\n✅ Rapport prospects 9h\n✅ Ping sitemap 7h\n✅ GMB posts 9h30\n✅ Google Ads copy mer. 8h\n✅ Audit SEO lun. 10h\n✅ LinkedIn posts 7h\n✅ Veille missions 8h30")

    elif text.startswith("/missions"):
        send(chat_id, "💼 MISSION URGENTE\n\n🔥 Senior UX/UI Designer\n📍 Saint-Denis (hybride 2j/sem)\n💰 600€/j max\n📅 Démarrage : avant 1er mai\n⏱ Durée : 2-3 ans\n\n→ Dis-moi \"postule à la mission\" pour préparer la candidature !")

    elif text.startswith("/reset"):
        conversation_history.pop(chat_id, None)
        send(chat_id, "🔄 Historique effacé.")

    elif text.startswith("/help"):
        send(chat_id, "🆘 AIDE\n\nCommandes :\n/rapport — Rapport express\n/status — Statut agents\n/missions — Missions freelance\n/reset — Effacer historique\n\nOu donne-moi une instruction directe, par exemple :\n• \"Publie un article sur le design system\"\n• \"Cherche des missions UX sur Malt\"\n• \"Rédige un message pour un prospect LinkedIn\"")

    elif text:
        send(chat_id, "⏳ Je traite ta demande...")
        thread = threading.Thread(target=run_agent, args=(chat_id, text))
        thread.daemon = True
        thread.start()

    return "OK", 200

@app.route("/")
def index():
    return "🤖 Dikenga Design Bot — Agent IA actif ✅"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
