import json
import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)
CORS(app)

# Récupère-la gratuitement sur : https://console.groq.com/keys
MA_CLE_API = os.environ.get("GROQ_API_KEY")

URL_API = "https://api.groq.com/openai/v1/chat/completions"

 #fonction pour ouvrire fichie json et transforme fiche en donne python (r= read)
def charger_connaissances():
    fichier = open("knowledge_base.json", "r", encoding="utf-8")
    donnees = json.load(fichier)
    fichier.close()
    return donnees


def chercher_info_utile(question, connaissances):
    question = question.lower()
    meilleure_fiche = None
    meilleur_score = 0

    for fiche in connaissances:
        texte = (fiche["titre"] + " " + fiche["contenu"]).lower()
        score = 0
        for mot in question.split():  # divise la question en mots
            if mot in texte: 
                score = score + 1
 #Cette partie compte les mots de la question qui se retrouvent dans chaque fiche, puis sélectionne la fiche 
 # qui en contient le plus pour l’utiliser comme contexte de la réponse
        if score > meilleur_score:
            meilleur_score = score
            meilleure_fiche = fiche

    return meilleure_fiche


def demander_a_groq(question, fiche, connaissances):
    if fiche is not None:
        contexte = fiche["titre"] + " : " + fiche["contenu"]
    else:
        # pour que le bot reste accueillant au lieu de dire "aucune info trouvée".
        resume_general = connaissances[0]["titre"] + " : " + connaissances[0]["contenu"]
        contexte = resume_general

    instructions = (
          "Tu es l'assistante virtuelle officielle de Ménara Université. "
        "\n\n"
        "RÈGLE DE PÉRIMÈTRE (la plus importante, à respecter STRICTEMENT) : "
        "tu ne réponds QU'AUX questions concernant Ménara Université "
        "(mission, valeurs, programmes, admissions, contact, campus, etc.). "
        "Si la question sort de ce sujet (mathématiques, culture générale, "
        "code, blagues, actualité, ou tout autre sujet non lié à l'université), "
        "tu dois REFUSER poliment de répondre et rediriger vers l'université, "
        "même si tu connais la réponse. "
        "Exemple : si on te demande '1+1 ?' ou 'raconte une blague', "
        "réponds quelque chose comme : "
        "'Je suis l'assistante de Ménara Université et je réponds uniquement "
        "aux questions sur l'université. Souhaitez-vous des informations sur "
        "nos programmes, notre mission, ou nos coordonnées ?' "
        "\n\n"
        "RÈGLE DE LANGUE : détecte la langue de la question "
        "et réponds UNIQUEMENT dans cette même langue (français, anglais ou arabe). "
        "\n\n"
        "Si l'utilisateur te salue simplement (bonjour, hello, salut), "
        "présente-toi brièvement et invite-le à poser une question sur l'université. "
        "\n\n"
        "Reste toujours en 2-4 phrases, naturelle et professionnelle. "
        "\n\n"
        "Contexte disponible sur l'université : " + contexte
    )

    headers = {
        "Authorization": "Bearer " + MA_CLE_API,
        "Content-Type": "application/json",
    }
    # une liste "messages" avec des rôles "system" et "user"
    donnees = {
        "model": "openai/gpt-oss-120b",
        "messages": [
            {"role": "system", "content": instructions},
            {"role": "user", "content": question},
        ],
    }

    reponse = requests.post(URL_API, headers=headers, json=donnees)
    #verifie si ila une erreur
    if reponse.status_code != 200:
        return "Erreur : " + reponse.text
    resultat = reponse.json()
    return resultat["choices"][0]["message"]["content"]

# ---- Le programme démarre ici ----

print("Chargement...")
connaissances = charger_connaissances()
print("Chatbot prêt ! (écris 'quit' pour arrêter)")

@app.route("/chat", methods=["POST"])
def chat(): 
    #recupere le message de frontend
    data = request.get_json(force=True)
    #enleve les espace de msg
    question = (data.get("message") or "").strip()
    if not question:#voir si le message vide si ila une error 
        return jsonify({"error": "Message vide"}), 400
    infos = chercher_info_utile(question, connaissances)
    reponse = demander_a_groq(question, infos, connaissances)
    #reourne la reponse a frontend
    return jsonify({"reponse": reponse})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
