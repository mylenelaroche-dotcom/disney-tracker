import os
import time
import requests
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)

ZAPIER_WEBHOOK = os.environ.get("ZAPIER_WEBHOOK", "")
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", "120"))  # secondes

WATCHLIST = [
    {
        "id": "space220",
        "type": "restaurant",
        "name": "Space 220 Lounge",
        "date": "2026-06-13",
        "start": "11:30",
        "end": "12:30",
        "party": 2,
    },
    {
        "id": "tower_terror",
        "type": "lightning",
        "name": "Twilight Zone Tower of Terror",
        "date": "2026-06-14",
        "start": "09:00",
        "end": "10:45",
        "party": 4,
    },
    {
        "id": "toy_story",
        "type": "lightning",
        "name": "Toy Story Mania",
        "date": "2026-06-14",
        "start": "09:00",
        "end": "10:45",
        "party": 4,
    },
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://disneyworld.disney.go.com/",
    "Origin": "https://disneyworld.disney.go.com",
}

found_items = set()


def time_in_range(t, start, end):
    if not t:
        return False
    t = t[:5]
    return start <= t <= end


def check_dining(item):
    url = (
        "https://disneyworld.disney.go.com/finder/api/v1/explorer-service/"
        "dining-availability-endpoint/wdw/en_US/tableservice/"
        f"{item['date']}/{item['party']}/1/false/"
    )
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        data = r.json()
        offers = data.get("offers") or data.get("availability", {}).get("offers", [])
        for offer in offers:
            name = (offer.get("facilityName") or offer.get("name") or "").lower()
            t = offer.get("time") or offer.get("startTime") or ""
            if item["name"].lower() in name and time_in_range(t, item["start"], item["end"]):
                return t
    except Exception as e:
        log.warning(f"Dining check error for {item['name']}: {e}")
    return None


def check_lightning(item):
    url = (
        "https://disneyworld.disney.go.com/entertainment/magic-kingdom/"
        f"lightning-lane/?date={item['date']}"
    )
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        data = r.json()
        slots = data.get("availability") or data.get("items") or []
        for slot in slots:
            name = (slot.get("name") or slot.get("facilityName") or "").lower()
            t = slot.get("startTime") or slot.get("time") or ""
            if item["name"].lower() in name and time_in_range(t, item["start"], item["end"]):
                return t
    except Exception as e:
        log.warning(f"Lightning check error for {item['name']}: {e}")
    return None


def notify(item, found_time):
    if not ZAPIER_WEBHOOK:
        log.error("ZAPIER_WEBHOOK non configuré!")
        return
    payload = {
        "event": "disney_availability_found",
        "item_name": item["name"],
        "item_type": item["type"],
        "date": item["date"],
        "time_found": found_time,
        "party_size": item["party"],
        "message": (
            f"DISPO DISNEY! {item['name']} "
            f"le {item['date']} a {found_time} "
            f"pour {item['party']} personnes. Réserve vite!"
        ),
    }
    try:
        r = requests.post(ZAPIER_WEBHOOK, json=payload, timeout=10)
        r.raise_for_status()
        log.info(f"Zapier notifié pour {item['name']} a {found_time}")
    except Exception as e:
        log.error(f"Erreur Zapier: {e}")


def check_all():
    active = [i for i in WATCHLIST if i["id"] not in found_items]
    if not active:
        log.info("Tous les créneaux trouvés. Monitoring terminé.")
        return False

    for item in active:
        log.info(f"Vérification: {item['name']} ({item['date']} {item['start']}-{item['end']})")
        found_time = None
        if item["type"] == "restaurant":
            found_time = check_dining(item)
        elif item["type"] == "lightning":
            found_time = check_lightning(item)

        if found_time:
            log.info(f"DISPO TROUVÉE: {item['name']} à {found_time}!")
            found_items.add(item["id"])
            notify(item, found_time)
        else:
            log.info(f"Aucune dispo pour {item['name']}")

    return True


def main():
    log.info("Disney Tracker démarré")
    log.info(f"Webhook Zapier: {'configuré' if ZAPIER_WEBHOOK else 'MANQUANT'}")
    log.info(f"Intervalle: {CHECK_INTERVAL}s · {len(WATCHLIST)} créneaux surveillés")

    while True:
        should_continue = check_all()
        if not should_continue:
            break
        log.info(f"Prochaine vérification dans {CHECK_INTERVAL}s...")
        time.sleep(CHECK_INTERVAL)

    log.info("Tracker arrêté — tous les créneaux ont été trouvés.")


if __name__ == "__main__":
    main()
