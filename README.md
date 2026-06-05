[README.md](https://github.com/user-attachments/files/28646309/README.md)
# Disney Availability Tracker — Guide de déploiement Render

## Ce que ça fait
Vérifie toutes les 2 minutes les disponibilités Disney et t'envoie un SMS via Zapier dès qu'un créneau se libère.

---

## Étape 1 — Crée un compte Render
1. Va sur https://render.com
2. Clique "Get Started for Free"
3. Connecte-toi avec Google (c'est le plus rapide)

---

## Étape 2 — Déploie le service

1. Dans Render, clique **"New +"** → **"Background Worker"**
2. Choisis **"Deploy an existing image or upload files"**
   - Si cette option n'est pas visible, choisis **"Web Service"** et suis les mêmes étapes
3. Upload les deux fichiers :
   - `tracker.py`
   - `requirements.txt`
4. Configure le service :
   - **Name** : `disney-tracker`
   - **Runtime** : `Python 3`
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `python tracker.py`
   - **Instance Type** : Free

---

## Étape 3 — Ajoute la variable d'environnement

Dans l'onglet **"Environment"** de ton service Render :

| Key | Value |
|-----|-------|
| `ZAPIER_WEBHOOK` | `https://hooks.zapier.com/hooks/catch/3180048/4bcxcdw/` |
| `CHECK_INTERVAL` | `120` |

> Ne jamais mettre l'URL webhook directement dans le code — Render la garde confidentielle dans les variables d'environnement.

---

## Étape 4 — Lance le service

Clique **"Deploy"**. Render installe les dépendances et démarre le tracker.

Dans l'onglet **"Logs"**, tu devrais voir :
```
Disney Tracker démarré
Webhook Zapier: configuré
Intervalle: 120s · 3 créneaux surveillés
Vérification: Space 220 Lounge...
```

---

## Modifier les créneaux surveillés

Ouvre `tracker.py` et édite la section `WATCHLIST` :

```python
WATCHLIST = [
    {
        "id": "identifiant_unique",       # pas d'espaces
        "type": "restaurant",              # ou "lightning"
        "name": "Nom exact de l'attraction",
        "date": "2026-06-13",             # format YYYY-MM-DD
        "start": "11:30",                  # heure min
        "end": "12:30",                    # heure max
        "party": 2,                        # nb de personnes
    },
]
```

---

## Arrêter le tracker

Dans Render → ton service → **"Suspend"**. Le service s'arrête automatiquement quand tous les créneaux sont trouvés.
