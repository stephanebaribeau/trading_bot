import os
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from alpaca.data.historical.news import NewsClient
from alpaca.data.requests import NewsRequest

TIME_ZONE = ZoneInfo("America/New_York")

load_dotenv()
client = NewsClient(os.getenv("ALPACA_API_KEY"), os.getenv("ALPACA_SECRET_KEY"))

requete = NewsRequest(
    symbols="AMD",
    start=datetime(2024,10,1),
    end=datetime(2024,11,1),
    sort="asc",
    limit=500,
)
articles = client.get_news(requete).data["news"]
print(f"{len(articles)} nouvelles en octobre 2024\n")

def moment(heure):
    """ Classe l'heure de publication par rapport à la séance de New York. """
    if heure.weekday() >= 5:
        return "fin de semaine"
    minutes = heure.hour * 60 + heure.minute
    if minutes < 9 * 60 + 30:
        return "avant l'ouverture"
    if minutes < 16 * 60:
        return "pendant la séance"
    return "après la fermeture"

def main():
    compteur = {}
    for article in articles:
        heure = article.created_at.astimezone(TIME_ZONE)
        m = moment(heure)
        compteur[m] = compteur.get(m, 0) + 1

        nb_symboles = len(article.symbols)
        print(f"{heure:%Y-%m-%d %H:%M}   [{m:<18}] ({nb_symboles} symboles)   {article.headline[:80]}")

    print(f"\n=== Moment de publication ===")
    for m, n in compteur.items():
        print(f"{m:<20} : {n}")

    seulement_amd = sum(1 for a in articles if a.symbols == ["AMD"])
    print(f"\nNouvelles qui concernent seulement AMD : {seulement_amd} and {len(articles)}")


if __name__ == "__main__":
    main()