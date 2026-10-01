import json
import re
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from urllib.parse import urljoin

import feedparser


# ============================================================
# SOURCES
# ============================================================

FEEDS = [

    # Généralistes
    (
        "lemonde",
        "Le Monde",
        ["inter", "societe", "climat", "eco"],
        "https://www.lemonde.fr/rss/une.xml",
        "https://www.lemonde.fr"
    ),

    (
        "midilibre",
        "Midi Libre",
        ["local", "societe"],
        "https://www.midilibre.fr/rss.xml",
        "https://www.midilibre.fr"
    ),

    # Médias indépendants / engagés
    (
        "mediapart",
        "Mediapart",
        ["inter", "societe", "eco", "droits"],
        "https://www.mediapart.fr/articles/feed",
        "https://www.mediapart.fr"
    ),

    (
        "politis",
        "Politis",
        ["societe", "droits", "climat", "inter"],
        "https://www.politis.fr/feed/",
        "https://www.politis.fr"
    ),

    (
        "blast",
        "BLAST",
        ["societe", "inter", "eco"],
        "https://www.blast-info.fr",
        "https://www.blast-info.fr"
    ),

    (
        "jours",
        "Les Jours",
        ["societe", "inter", "eco"],
        "https://lesjours.fr",
        "https://lesjours.fr"
    ),

    (
        "humanite",
        "L'Humanité",
        ["societe", "eco", "inter"],
        "https://www.humanite.fr",
        "https://www.humanite.fr"
    ),

    (
        "mondediplo",
        "Le Monde diplomatique",
        ["inter", "eco", "societe"],
        "https://www.monde-diplomatique.fr",
        "https://www.monde-diplomatique.fr"
    ),

    # Écologie
    (
        "reporterre",
        "Reporterre",
        ["climat", "societe"],
        "https://reporterre.net/spip.php?page=backend-simple",
        "https://reporterre.net"
    ),

    (
        "vert",
        "Vert",
        ["climat", "societe"],
        "https://vert.eco/feed",
        "https://vert.eco"
    ),

    (
        "bonpote",
        "Bon Pote",
        ["climat"],
        "https://bonpote.com/feed/",
        "https://bonpote.com"
    ),

    # Économie / société
    (
        "altereco",
        "Alternatives économiques",
        ["eco", "societe"],
        "https://www.alternatives-economiques.fr/rss.xml",
        "https://www.alternatives-economiques.fr"
    ),

    (
        "basta",
        "Basta!",
        ["societe", "droits", "eco"],
        "https://basta.media/spip.php?page=backend",
        "https://basta.media"
    ),

    # Investigation / lanceurs d'alerte
    (
        "disclose",
        "Disclose",
        ["alerte", "societe", "droits"],
        "https://disclose.ngo/fr",
        "https://disclose.ngo/fr"
    ),

    (
        "mla",
        "Maison des Lanceurs d'Alerte",
        ["alerte", "droits"],
        "https://mlalerte.org/feed/",
        "https://mlalerte.org"
    ),

    (
        "acrimed",
        "Acrimed",
        ["societe", "inter"],
        "https://www.acrimed.org/spip.php?page=backend",
        "https://www.acrimed.org"
    ),

    # Droits humains / institutions / associations
    (
        "amnesty",
        "Amnesty France",
        ["droits", "inter"],
        "https://www.amnesty.fr/rss",
        "https://www.amnesty.fr"
    ),

    (
        "onu",
        "ONU Info",
        ["inter", "droits", "climat"],
        "https://news.un.org/feed/subscribe/fr/news/all/rss.xml",
        "https://news.un.org/fr"
    ),

    (
        "greenpeace",
        "Greenpeace France",
        ["climat", "alerte"],
        "https://www.greenpeace.fr/feed/",
        "https://www.greenpeace.fr"
    ),
]


# Nombre maximum d'articles récupérés par source
PAR_SOURCE = 15

# Nombre maximum d'articles dans data.json
MAX_ITEMS = 400

USER_AGENT = (
    "Mozilla/5.0 "
    "(compatible; LeFil/1.0; +https://github.com/)"
)


# ============================================================
# OUTILS
# ============================================================

def get(url):
    """Télécharge une URL avec un User-Agent."""
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT}
    )

    with urllib.request.urlopen(request, timeout=25) as response:
        return response.read()


def clean_html(text):
    """Supprime les balises HTML d'un texte."""
    if not text:
        return ""

    text = unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def parse_date(value):
    """Transforme différentes dates RSS/Atom en datetime UTC."""

    if not value:
        return None

    try:
        date = parsedate_to_datetime(value)

    except Exception:

        try:
            date = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )

        except Exception:
            return None

    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)

    return date.astimezone(timezone.utc)


def entry_date(entry):
    """Récupère la meilleure date disponible dans un article."""

    for key in (
        "published",
        "updated",
        "created",
        "date"
    ):
        value = entry.get(key)

        if value:
            parsed = parse_date(value)

            if parsed:
                return parsed

    # feedparser possède parfois déjà la date sous forme struct_time
    for key in (
        "published_parsed",
        "updated_parsed"
    ):
        value = entry.get(key)

        if value:
            try:
                return datetime(
                    *value[:6],
                    tzinfo=timezone.utc
                )
            except Exception:
                pass

    return None


def entry_link(entry, base):
    """Récupère le lien principal d'un article."""

    link = entry.get("link")

    if link:
        return urljoin(base, link)

    for item in entry.get("links", []):
        href = item.get("href")

        if href and item.get("rel", "alternate") == "alternate":
            return urljoin(base, href)

    return ""


def entry_image(entry, base):
    """Essaie de récupérer l'image principale."""

    # Media RSS
    for item in entry.get("media_content", []):
        url = item.get("url")

        if url:
            return urljoin(base, url)

    # Thumbnail
    for item in entry.get("media_thumbnail", []):
        url = item.get("url")

        if url:
            return urljoin(base, url)

    # Enclosures
    for item in entry.get("enclosures", []):
        url = item.get("href") or item.get("url")
        mime = item.get("type", "")

        if url and (
            mime.startswith("image/")
            or re.search(
                r"\.(jpe?g|png|webp)(\?|$)",
                url,
                re.I
            )
        ):
            return urljoin(base, url)

    # Image dans le contenu HTML
    html = ""

    for key in (
        "summary",
        "description",
        "content"
    ):
        value = entry.get(key)

        if isinstance(value, list):
            for item in value:
                html += item.get("value", "")

        elif isinstance(value, str):
            html += value

    html = unescape(html)

    match = re.search(
        r'<img[^>]+src=["\']([^"\']+)',
        html,
        re.I
    )

    if match:
        return urljoin(base, match.group(1))

    return ""


# ============================================================
# DÉCOUVERTE AUTOMATIQUE DES RSS
# ============================================================

def discover_feed(site):
    """
    Cherche automatiquement un flux RSS/Atom déclaré
    dans le HTML du site.
    """

    html = get(site).decode(
        "utf-8",
        "ignore"
    )

    patterns = [
        r'<link[^>]+type=["\']application/rss\+xml["\'][^>]*>',
        r'<link[^>]+type=["\']application/atom\+xml["\'][^>]*>',
        r'<link[^>]+type=["\']application/xml\+rss["\'][^>]*>',
    ]

    for pattern in patterns:

        for match in re.finditer(
            pattern,
            html,
            re.I
        ):
            tag = match.group(0)

            href = re.search(
                r'href=["\']([^"\']+)',
                tag,
                re.I
            )

            if href:
                return urljoin(
                    site,
                    href.group(1)
                )

    return None


# ============================================================
# CHARGEMENT D'UN FLUX
# ============================================================

def load_feed(url, site):

    candidates = []

    # URL indiquée dans FEEDS
    candidates.append(url)

    # Quelques chemins classiques
    candidates.extend([
        site.rstrip("/") + "/feed/",
        site.rstrip("/") + "/feed",
        site.rstrip("/") + "/rss",
        site.rstrip("/") + "/rss.xml",
        site.rstrip("/") + "/feed.xml",
    ])

    # Découverte automatique
    try:
        discovered = discover_feed(site)

        if discovered:
            candidates.append(discovered)

    except Exception:
        pass

    # Supprime les doublons
    candidates = list(dict.fromkeys(candidates))

    errors = []

    for candidate in candidates:

        try:
            data = get(candidate)

            parsed = feedparser.parse(data)

            if parsed.entries:

                return (
                    parsed.entries,
                    candidate,
                    ""
                )

        except Exception as error:

            errors.append(
                type(error).__name__
            )

    return (
        [],
        url,
        ", ".join(errors)
        if errors
        else "aucun article trouvé"
    )


# ============================================================
# PROGRAMME PRINCIPAL
# ============================================================

def main():

    now = datetime.now(timezone.utc)

    all_items = []
    status = []

    seen_links = set()

    for (
        feed_id,
        name,
        themes,
        feed_url,
        site
    ) in FEEDS:

        print(f"→ {name}")

        entries, used_url, error = load_feed(
            feed_url,
            site
        )

        # Tri du plus récent au plus ancien
        entries.sort(
            key=lambda entry:
                entry_date(entry)
                or datetime.min.replace(
                    tzinfo=timezone.utc
                ),
            reverse=True
        )

        count = 0

        for entry in entries[:PAR_SOURCE]:

            title = clean_html(
                entry.get("title", "")
            )

            link = entry_link(
                entry,
                site
            )

            if not title or not link:
                continue

            # Évite les doublons
            if link in seen_links:
                continue

            seen_links.add(link)

            date = (
                entry_date(entry)
                or now
            )

            image = entry_image(
                entry,
                site
            )

            all_items.append({
                "source": name,
                "sid": feed_id,
                "themes": themes,
                "title": title,
                "link": link,
                "image": image,
                "date": date.isoformat()
            })

            count += 1

        status.append({
            "name": name,
            "ok": bool(entries),
            "count": count,
            "url": used_url,
            "error": error
        })

        print(
            f"   {count} article(s)"
        )

    # Tri global
    all_items.sort(
        key=lambda item: item["date"],
        reverse=True
    )

    # Écriture du fichier utilisé par index.html
    with open(
        "data.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            {
                "updated": now.isoformat(),
                "status": status,
                "items": all_items[:MAX_ITEMS]
            },
            file,
            ensure_ascii=False,
            indent=2
        )

    successful = sum(
        1
        for source in status
        if source["ok"]
    )

    print()
    print(
        f"{successful}/{len(status)} "
        "flux ont répondu."
    )


if __name__ == "__main__":
    main()