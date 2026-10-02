import json, re, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from urllib.parse import urljoin
import feedparser

THEMES = [
    ("climat", "Climat et écologie"), ("droits", "Droits humains"),
    ("inter", "International"), ("societe", "Société"),
    ("eco", "Économie et travail"), ("justice", "Justice et libertés"),
    ("alerte", "Lanceurs d’alerte"), ("sante", "Santé"),
    ("numerique", "Numérique et médias"), ("data", "Chiffres officiels"),
    ("local", "Local"),
]

# (id, nom, catégorie, thèmes, adresse du flux, site)
P, I, E, N, A, O = "Presse", "Indépendants", "Écologie", "Enquête", "Associations et ONG", "Institutions et chiffres"
FEEDS = [
 ("lemonde","Le Monde",P,["inter","societe","climat","eco"],"https://www.lemonde.fr/rss/une.xml","https://www.lemonde.fr"),
 ("liberation","Libération",P,["societe","inter","justice"],"https://www.liberation.fr/arc/outboundfeeds/rss-all/collection/accueil-une/?outputType=xml","https://www.liberation.fr"),
 ("humanite","L'Humanité",P,["societe","eco","inter"],"https://www.humanite.fr/feed","https://www.humanite.fr"),
 ("mondediplo","Le Monde diplomatique",P,["inter","eco","societe"],"https://www.monde-diplomatique.fr/rss","https://www.monde-diplomatique.fr"),
 ("courrierint","Courrier international",P,["inter"],"https://www.courrierinternational.com/feed/all/rss.xml","https://www.courrierinternational.com"),
 ("altereco","Alternatives économiques",P,["eco","societe"],"https://www.alternatives-economiques.fr/rss.xml","https://www.alternatives-economiques.fr"),
 ("midilibre","Midi Libre",P,["local","societe"],"https://www.midilibre.fr/rss.xml","https://www.midilibre.fr"),
 ("mediapart","Mediapart",I,["societe","justice","inter","eco"],"https://www.mediapart.fr/articles/feed","https://www.mediapart.fr"),
 ("politis","Politis",I,["societe","droits","climat","inter"],"https://www.politis.fr/feed/","https://www.politis.fr"),
 ("blast","Blast",I,["societe","inter","eco"],"https://www.blast-info.fr/feed","https://www.blast-info.fr"),
 ("lesjours","Les Jours",I,["societe","justice","inter"],"https://lesjours.fr/feed","https://lesjours.fr"),
 ("basta","Basta!",I,["societe","droits","eco"],"https://basta.media/spip.php?page=backend","https://basta.media"),
 ("streetpress","StreetPress",I,["societe","droits","justice"],"https://www.streetpress.com/rss","https://www.streetpress.com"),
 ("lemedia","Le Média",I,["societe","inter"],"https://lemediatv.fr/feed","https://lemediatv.fr"),
 ("asi","Arrêt sur images",I,["numerique","societe"],"https://api.arretsurimages.net/api/public/rss/all-content","https://www.arretsurimages.net"),
 ("acrimed","Acrimed",I,["numerique","societe"],"https://www.acrimed.org/spip.php?page=backend","https://www.acrimed.org"),
 ("rdf","Rapports de Force",I,["eco","societe"],"https://rapportsdeforce.fr/feed","https://rapportsdeforce.fr"),
 ("frustration","Frustration",I,["societe","eco"],"https://frustrationmagazine.fr/feed","https://frustrationmagazine.fr"),
 ("deferlante","La Déferlante",I,["societe","droits"],"https://revuedeferlante.fr/feed","https://revuedeferlante.fr"),
 ("ballast","Ballast",I,["societe","eco","climat"],"https://www.revue-ballast.fr/feed","https://www.revue-ballast.fr"),
 ("ventseleve","Le Vent Se Lève",I,["eco","inter","societe"],"https://lvsl.fr/feed","https://lvsl.fr"),
 ("contretemps","Contretemps",I,["eco","societe"],"https://www.contretemps.eu/feed","https://www.contretemps.eu"),
 ("mrmondia","Mr Mondialisation",I,["climat","societe"],"https://mrmondialisation.org/feed","https://mrmondialisation.org"),
 ("orientxxi","Orient XXI",I,["inter","droits"],"https://orientxxi.info/spip.php?page=backend","https://orientxxi.info"),
 ("conversation","The Conversation France",I,["societe","sante","climat","eco"],"https://theconversation.com/fr/articles.atom","https://theconversation.com/fr"),
 ("bonpote","Bon Pote",E,["climat"],"https://bonpote.com/feed/","https://bonpote.com"),
 ("reporterre","Reporterre",E,["climat","societe"],"https://reporterre.net/spip.php?page=backend-simple","https://reporterre.net"),
 ("vert","Vert",E,["climat","societe"],"https://vert.eco/feed","https://vert.eco"),
 ("rac","Réseau Action Climat",E,["climat"],"https://reseauactionclimat.org/feed/","https://reseauactionclimat.org"),
 ("ademe","Ademe",E,["climat","data"],"https://presse.ademe.fr/feed","https://presse.ademe.fr"),
 ("disclose","Disclose",N,["alerte","societe","justice"],"https://disclose.ngo/fr/feed","https://disclose.ngo"),
 ("mediacites","Médiacités",N,["local","justice","alerte"],"https://www.mediacites.fr/feed","https://www.mediacites.fr"),
 ("multinationales","Observatoire des multinationales",N,["eco","alerte"],"https://multinationales.org/spip.php?page=backend","https://multinationales.org"),
 ("reflets","Reflets",N,["numerique","alerte"],"https://reflets.info/feeds/public","https://reflets.info"),
 ("next","Next",N,["numerique","droits"],"https://next.ink/feed","https://next.ink"),
 ("mla","Maison des Lanceurs d'Alerte",N,["alerte","droits"],"https://mlalerte.org/feed/","https://mlalerte.org"),
 ("pplaaf","PPLAAF",N,["alerte","droits","inter"],"https://www.pplaaf.org/feed","https://www.pplaaf.org"),
 ("tifr","Transparency International France",N,["alerte","justice","eco"],"https://transparency-france.org/feed/","https://transparency-france.org"),
 ("anticor","Anticor",N,["alerte","justice"],"https://www.anticor.org/feed","https://www.anticor.org"),
 ("sherpa","Sherpa",N,["alerte","justice","eco"],"https://www.asso-sherpa.org/feed","https://www.asso-sherpa.org"),
 ("amnesty","Amnesty France",A,["droits","inter","alerte"],"https://www.amnesty.fr/rss","https://www.amnesty.fr"),
 ("hrw","Human Rights Watch",A,["droits","inter"],"https://www.hrw.org/fr/rss","https://www.hrw.org/fr"),
 ("ldh","Ligue des droits de l'Homme",A,["droits","justice"],"https://www.ldh-france.org/feed/","https://www.ldh-france.org"),
 ("rsf","Reporters sans frontières",A,["droits","numerique"],"https://rsf.org/fr/rss.xml","https://rsf.org/fr"),
 ("greenpeace","Greenpeace France",A,["climat","alerte"],"https://www.greenpeace.fr/feed/","https://www.greenpeace.fr"),
 ("oxfam","Oxfam France",A,["eco","inter","droits"],"https://www.oxfamfrance.org/feed/","https://www.oxfamfrance.org"),
 ("attac","Attac France",A,["eco","societe"],"https://france.attac.org/spip.php?page=backend","https://france.attac.org"),
 ("fap","Fondation pour le logement",A,["societe"],"https://www.fondationpourlelogement.fr/feed/","https://www.fondationpourlelogement.fr"),
 ("quadrature","La Quadrature du Net",A,["numerique","droits","justice"],"https://www.laquadrature.net/feed/","https://www.laquadrature.net"),
 ("msf","Médecins sans frontières",A,["sante","inter","droits"],"https://www.msf.fr/rss.xml","https://www.msf.fr"),
 ("onu","ONU Info",O,["inter","droits","climat"],"https://news.un.org/feed/subscribe/fr/news/all/rss.xml","https://news.un.org/fr"),
 ("insee","Insee",O,["data","eco","societe"],"https://www.insee.fr/fr/rss","https://www.insee.fr"),
 ("eurostat","Eurostat",O,["data","eco"],"https://ec.europa.eu/eurostat/web/main/news/rss","https://ec.europa.eu/eurostat"),
 ("sante_publique","Santé publique France",O,["sante","data"],"https://www.santepubliquefrance.fr/rss","https://www.santepubliquefrance.fr"),
 ("oms","OMS",O,["sante","inter"],"https://www.who.int/rss-feeds/news-french.xml","https://www.who.int/fr"),
 ("cnil","CNIL",O,["numerique","droits","justice"],"https://www.cnil.fr/fr/rss.xml","https://www.cnil.fr"),
 ("ddd","Défenseur des droits",O,["droits","justice"],"https://www.defenseurdesdroits.fr/rss.xml","https://www.defenseurdesdroits.fr"),
 ("cdc","Cour des comptes",O,["data","eco","justice"],"https://www.ccomptes.fr/fr/rss.xml","https://www.ccomptes.fr"),
 ("vieP","Vie publique",O,["justice","societe","data"],"https://www.vie-publique.fr/rss","https://www.vie-publique.fr"),
 ("inegalites","Observatoire des inégalités",O,["data","societe","eco"],"https://www.inegalites.fr/spip.php?page=backend","https://www.inegalites.fr"),
 ("cnrs","CNRS Le journal",O,["sante","climat","societe"],"https://lejournal.cnrs.fr/rss","https://lejournal.cnrs.fr"),
]

PAR_SOURCE = 10
MAX_ITEMS = 800
UA = "Mozilla/5.0 (compatible; LeFil/1.0)"

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read()

def clean(t):
    if not t: return ""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", unescape(t))).strip()

def parse_date(v):
    if not v: return None
    try: d = parsedate_to_datetime(v)
    except Exception:
        try: d = datetime.fromisoformat(v.replace("Z", "+00:00"))
        except Exception: return None
    if d.tzinfo is None: d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)

def entry_date(e):
    for k in ("published_parsed", "updated_parsed"):
        v = e.get(k)
        if v:
            try: return datetime(*v[:6], tzinfo=timezone.utc)
            except Exception: pass
    for k in ("published", "updated", "created", "date"):
        d = parse_date(e.get(k))
        if d: return d
    return None

def entry_link(e, base):
    if e.get("link"): return urljoin(base, e["link"])
    for l in e.get("links", []):
        if l.get("href"): return urljoin(base, l["href"])
    return ""

def entry_image(e, base):
    for k in ("media_content", "media_thumbnail"):
        for m in e.get(k, []):
            if m.get("url"): return urljoin(base, m["url"])
    for m in e.get("enclosures", []):
        u = m.get("href") or m.get("url")
        if u and (m.get("type", "").startswith("image/") or re.search(r"\.(jpe?g|png|webp)", u, re.I)):
            return urljoin(base, u)
    html = ""
    for k in ("summary", "description", "content"):
        v = e.get(k)
        if isinstance(v, list): html += "".join(x.get("value", "") for x in v)
        elif isinstance(v, str): html += v
    m = re.search(r'<img[^>]+src=["\']([^"\']+)', unescape(html), re.I)
    return urljoin(base, m.group(1)) if m else ""

def discover(site):
    html = get(site).decode("utf-8", "ignore")
    for m in re.finditer(r"<link[^>]+>", html, re.I):
        tag = m.group(0)
        if re.search(r"application/(rss|atom)\+xml", tag, re.I):
            h = re.search(r'href=["\']([^"\']+)', tag)
            if h: return urljoin(site, h.group(1))
    return None

def load(url, site):
    tried = []
    for step in ("direct", "decouverte"):
        try:
            u = url if step == "direct" else discover(site)
            if not u or u in tried: continue
            tried.append(u)
            entries = feedparser.parse(get(u)).entries
            if entries: return entries, u, ""
        except Exception as ex:
            tried.append(type(ex).__name__)
    return [], url, "aucun flux lisible"

def work(feed):
    fid, name, kind, themes, url, site = feed
    entries, used, err = load(url, site)
    entries.sort(key=lambda e: entry_date(e) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    now = datetime.now(timezone.utc)
    items = []
    for e in entries[:PAR_SOURCE]:
        title, link = clean(e.get("title", "")), entry_link(e, site)
        if not title or not link: continue
        items.append({"source": name, "sid": fid, "kind": kind, "themes": themes, "title": title,
                      "link": link, "image": entry_image(e, site),
                      "date": (entry_date(e) or now).isoformat()})
    return items, {"name": name, "kind": kind, "ok": bool(items), "count": len(items), "url": used, "error": err}

def main():
    now = datetime.now(timezone.utc)
    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(work, FEEDS))
    seen, items, status = set(), [], []
    for its, st in results:
        status.append(st)
        for i in its:
            if i["link"] in seen: continue
            seen.add(i["link"]); items.append(i)
    items.sort(key=lambda i: i["date"], reverse=True)
    kinds = list(dict.fromkeys(f[2] for f in FEEDS))
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump({"updated": now.isoformat(), "themes": THEMES, "kinds": kinds,
                   "status": status, "items": items[:MAX_ITEMS]}, f, ensure_ascii=False)
    print(sum(s["ok"] for s in status), "/", len(status), "flux ont répondu;", len(items), "articles")

if __name__ == "__main__":
    main()
