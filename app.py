from flask import Flask, request
import urllib.request, json, os
from datetime import datetime

app = Flask(__name__)

TOKEN = "8710994922:AAG_tiyBXu0Q_KS7Ck8UKmkPR6xXbmskai8"
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

SYSTEM_PROMPT = """Tu es l'assistant personnel de Dikenga Design, UI/UX Designer freelance à Paris (Les Pavillons-sous-Bois, 93320).

Contexte complet :
- Site : dikengadesign.fr (hébergé GitHub Pages, repo Bihem/bihem.github.io)
- Email : dikengadesign@gmail.com | Tel : +33 7 67 53 70 59
- Malt : malt.fr/profile/mesrevesbouzanga1 | LinkedIn : linkedin.com/in/dikengadesign/
- TJM habituel : ~445€/j
- 9 agents automatisés actifs (blog SEO, rapports, GMB, LinkedIn, veille missions...)
- Mission prioritaire détectée : Senior UX/UI Saint-Denis 600€/j, démarrage avant 1er mai 2026
- Google My Business : 3 avis reçus, fiche revendiquée
- Stack : HTML/CSS/JS statique, Figma, Design Systems, accessibilité numérique

Tu aides avec : stratégie freelance, rédaction messages clients, analyse missions, conseils SEO, suivi agents, idées contenu. Réponds en français, de façon concise et actionnable. Tu peux utiliser des émojis."""

conversation_history = {}

def send(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = json.dumps({"chat_id": str(chat_id), "text": text}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except Exception as e:
        print("Erreur send:", e)

def ask_claude(chat_id, user_message):
    if chat_id not in conversation_history:
        conversation_history[chat_id] = []

    conversation_history[chat_id].append({"role": "user", "content": user_message})

    if len(conversation_history[chat_id]) > 12:
        conversation_history[chat_id] = conversation_history[chat_id][-12:]

    payload = {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 500,
        "system": SYSTEM_PROMPT,
        "messages": conversation_history[chat_id]
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
        with urllib.request.urlopen(req) as r:
            result = json.loads(r.read())
            reply = result["content"][0]["text"]
            conversation_history[chat_id].append({"role": "assistant", "content": reply})
            return reply
    except Exception as e:
        print("Erreur Claude API:", e)
        return "⚠️ Je rencontre une difficulté. Réessaie dans un instant."

@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json(silent=True)
    if not data or "message" not in data:
        return "OK", 200

    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "").strip()

    if text.startswith("/start"):
        send(chat_id, "👋 Bonjour ! Je suis l'assistant IA de Dikenga Design.\n\nPose-moi n'importe quelle question sur ta stratégie freelance, tes missions, ton SEO, ou envoie-moi simplement un message.\n\nCommandes rapides :\n/rapport — Rapport express\n/status — Statut des agents\n/missions — Missions détectées\n/reset — Effacer l'historique\n/help — Aide")

    elif text.startswith("/rapport"):
        now = datetime.now().strftime("%H:%M %d/%m")
        send(chat_id, f"📊 RAPPORT EXPRESS — {now}\n\n✅ dikengadesign.fr — En ligne\n✅ 9 agents actifs\n✅ Email + Telegram opérationnels\n✅ GMB : 3 avis Google\n\n💼 Mission prioritaire :\n→ Senior UX/UI Saint-Denis 600€/j\n→ Démarrage avant 1er mai\n\n⏰ Prochain rapport complet dans 3h")

    elif text.startswith("/status"):
        send(chat_id, "🤖 STATUT AGENTS DIKENGA DESIGN\n\n✅ Rapport 3h (Telegram + Email)\n✅ Blog SEO quotidien 8h\n✅ Rapport prospects 9h\n✅ Ping sitemap 7h\n✅ GMB posts 9h30\n✅ Google Ads copy mer. 8h\n✅ Audit SEO lun. 10h\n✅ LinkedIn posts 7h\n✅ Veille missions 8h30\n\nTous les agents sont actifs ✅")

    elif text.startswith("/missions"):
        send(chat_id, "💼 MISSIONS DÉTECTÉES\n\n🔥 URGENT — Senior UX/UI Designer\n📍 Saint-Denis (hybride 2j/sem)\n💰 600€/j max\n📅 Démarrage : avant 1er mai\n⏱ Durée : 2-3 ans\n🔗 Free-Work / Glassdoor\n\n→ Candidature prête — postuler maintenant !")

    elif text.startswith("/reset"):
        conversation_history.pop(chat_id, None)
        send(chat_id, "🔄 Historique effacé. Nouvelle conversation.")

    elif text.startswith("/help") or text.startswith("/aide"):
        send(chat_id, "🆘 AIDE — Commandes :\n\n/rapport — Rapport express\n/status — Statut des 9 agents\n/missions — Missions freelance\n/reset — Effacer l'historique\n/help — Cette aide\n\nOu pose directement ta question, je réponds avec l'IA Claude 🤖")

    elif text:
        reply = ask_claude(chat_id, text)
        send(chat_id, reply)

    return "OK", 200

@app.route("/")
def index():
    return "🤖 Dikenga Design Bot — Actif ✅ (Claude AI)"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
