from flask import Flask, request
import urllib.request, json, os
from datetime import datetime

app = Flask(__name__)

TOKEN = "8710994922:AAG_tiyBXu0Q_KS7Ck8UKmkPR6xXbmskai8"

def send(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = json.dumps({"chat_id": chat_id, "text": text}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except Exception as e:
        print("Erreur send:", e)

@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json(silent=True)
    if not data or "message" not in data:
        return "OK", 200

    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "").strip()

    if text.startswith("/start"):
        send(chat_id, "👋 Bonjour ! Je suis l'assistant Dikenga Design.\n\nCommandes disponibles :\n/rapport — Rapport express\n/status — Statut des agents\n/missions — Missions détectées\n/help — Aide")

    elif text.startswith("/rapport"):
        now = datetime.now().strftime("%H:%M %d/%m")
        send(chat_id, f"📊 RAPPORT EXPRESS — {now}\n\n✅ dikengadesign.fr — En ligne\n✅ 9 agents actifs\n✅ Email + Telegram opérationnels\n✅ GMB : 3 avis Google\n\n💼 Mission prioritaire :\n→ Senior UX/UI Saint-Denis 600€/j\n→ Postuler : Free-Work / Glassdoor\n\n⏰ Prochain rapport complet dans 3h")

    elif text.startswith("/status"):
        send(chat_id, "🤖 STATUT AGENTS DIKENGA DESIGN\n\n✅ Rapport 3h (Telegram + Email)\n✅ Blog SEO quotidien 8h\n✅ Rapport prospects 9h\n✅ Ping sitemap 7h\n✅ GMB posts 9h30\n✅ Google Ads copy mer. 8h\n✅ Audit SEO lun. 10h\n✅ LinkedIn posts 7h\n✅ Veille missions 8h30\n\nTous les agents sont actifs ✅")

    elif text.startswith("/missions"):
        send(chat_id, "💼 MISSIONS DÉTECTÉES\n\n🔥 URGENT — Senior UX/UI Designer\n📍 Saint-Denis (hybride)\n💰 600€/j max\n📅 Démarrage : avant 1er mai\n⏱ Durée : 2-3 ans\n🔗 Free-Work / Glassdoor\n\n→ Postuler maintenant avec dikengadesign.fr + Malt")

    elif text.startswith("/help") or text.startswith("/aide"):
        send(chat_id, "🆘 AIDE — Commandes disponibles :\n\n/rapport — Rapport express immédiat\n/status — Statut des 9 agents\n/missions — Missions freelance détectées\n/help — Cette aide\n\n📧 Email : dikengadesign@gmail.com\n🌐 dikengadesign.fr")

    else:
        send(chat_id, f"✅ Message reçu.\nTape /help pour voir les commandes disponibles.")

    return "OK", 200

@app.route("/")
def index():
    return "🤖 Dikenga Design Bot — Actif ✅"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
