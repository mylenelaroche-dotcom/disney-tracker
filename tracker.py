import os
import time
import requests
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)

ZAPIER_WEBHOOK = os.environ.get("ZAPIER_WEBHOOK", "")
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", "10"))
DISNEY_COOKIES = os.environ.get("DISNEY_COOKIES", "")

WATCHLIST = [
    {
        "id": "space220",
        "type": "restaurant",
        "name": "Space 220 Lounge",
        "facility_id": "19634138",
        "date": "2026-06-13",
        "start": "11:30",
        "end": "12:30",
        "party": 2,
    },
]

def get_headers():
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-CA,en;q=0.9",
        "Referer": "https://disneyworld.disney.go.com/dining/epcot/space-220-restaurant/",
    }
    if DISNEY_COOKIES:
        headers["Cookie"] = DISNEY_COOKIES
    return headers

found_items = set()


def time_in_range(t, start, end):
    if not t:
        return False
    t = t[:5]
    return start <= t <= end


def check_dining(item):
    url = (
        f"https://disneyworld.disney.go.com/dine-res/api/availability/"
        f"{item['party']}/{item['date']},{item['date']}"
        f"?facilityId={item['facility_id']};entityType=restaurant"
        f"&entityType=restaurant"
    )
    try:
        r = requests.get(url, headers=get_headers(), timeout=15)
        r.raise_for_status()
        data = r.json()
        log.info(f"Réponse reçue: {str(data)[:300]}")

        offers = []
        if isinstance(data, list):
            offers = data
        elif isinstance(data, dict):
            offers = (
                data.get("offers")
                or data.get("availability")
                or data.get("times")
                or data.get("slots")
                or []
            )

        for offer in offers:
            t = (
                offer.get("time")
                or offer.get("startTime")
                or offer.get("offerTime")
                or offer.get("dateTime")
                or ""
            )
            if time_in_range(t, item["start"], item["end"]):
                return t

        if offers:
            log.info(f"Créneaux trouvés mais hors plage {item['start']}-{item['end']}")
        else:
            log.info(f"Aucun créneau disponible")

    except Exception as e:
        log.warning(f"Erreur pour {item['name']}: {e}")
    return None


def notify(item, found_time):
    if not ZAPIER_WEBHOOK:
        log.error("ZAPIER_WEBHOOK non configuré!")
        return
    payload = {
        "event": "disney_availability_found",
        "item_name": item["name"],
        "date": item["date"],
        "time_found": found_time,
        "party_size": item["party"],
        "message": (
            f"DISPO DISNEY! {item['name']} "
            f"le {item['date']} a {found_time} "
            f"pour {item['party']} personnes. Reserve vite!"
        ),
    }
    try:
        r = requests.post(ZAPIER_WEBHOOK, json=payload, timeout=10)
        r.raise_for_status()
        log.info(f"Zapier notifie pour {item['name']} a {found_time}")
    except Exception as e:
        log.error(f"Erreur Zapier: {e}")


def check_all():
    active = [i for i in WATCHLIST if i["id"] not in found_items]
    if not active:
        log.info("Tous les creneaux trouves. Monitoring termine.")
        return False

    for item in active:
        log.info(f"Verification: {item['name']} ({item['date']} {item['start']}-{item['end']})")
        found_time = check_dining(item)

        if found_time:
            log.info(f"DISPO TROUVEE: {item['name']} a {found_time}!")
            found_items.add(item["id"])
            notify(item, found_time)

    return True


def main():
    log.info("Disney Tracker demarre")
    log.info(f"Webhook Zapier: {'configure' if ZAPIER_WEBHOOK else 'MANQUANT'}")
    log.info(f"Cookies Disney: {'presents' if DISNEY_COOKIES else 'MANQUANTS'}")
    log.info(f"Intervalle: {CHECK_INTERVAL}s * {len(WATCHLIST)} creneaux surveilles")

    while True:
        should_continue = check_all()
        if not should_continue:
            break
        log.info(f"Prochaine verification dans {CHECK_INTERVAL}s...")
        time.sleep(CHECK_INTERVAL)

    log.info("Tracker arrete.")


if __name__ == "__main__":
    main()
