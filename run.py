"""
Robot du Events Tracker.
GitHub le lance automatiquement (voir .github/workflows/robot.yml).

Ce qu'il fait à chaque passage :
  1. lit la liste des sources dans sources.json ;
  2. pour chaque plateforme de recrutement (tal.net, Workday, Oracle) : repère les nouveaux
     events et spring weeks, lit leur page, devine le type, la ville et les dates,
     puis les ajoute dans Supabase ;
  3. pour les pages fixes : regarde si le texte a changé depuis la dernière fois ;
  4. t'envoie UN mail récapitulatif s'il y a du nouveau (nouvel event, page modifiée, source cassée) ;
  5. le lundi matin, t'envoie en plus le récap des deadlines des 14 prochains jours.

Tu n'as rien à modifier ici pour que ça marche : les clés sont lues dans les "Secrets" GitHub.
"""

import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# ---------- Réglages lus dans les Secrets GitHub ----------
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SECRET_KEY = os.environ.get("SUPABASE_SECRET_KEY", "")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
ALERT_EMAIL = os.environ.get("ALERT_EMAIL", "")
SITE_URL = os.environ.get("SITE_URL", "")
DRY_RUN = os.environ.get("DRY_RUN") == "1"   # 1 = mode test : n'écrit rien, affiche tout ce qui serait ajouté
ONLY = os.environ.get("ONLY", "").strip()    # mode test : ne lancer qu'une source (son id)

HEADERS_WEB = {"User-Agent": "Mozilla/5.0 (EventsTracker; usage personnel, 1 passage / 30 min)"}
MAX_NEW_PAGES_PER_SOURCE = 25   # limite de pages d'events lues par source et par passage (politesse)

# ---------- Mots-clés ----------
# Un lien est gardé seulement s'il ressemble à un EVENT, et pas à un stage ou à un apprentissage.
EVENT_WORDS = ["insight", "event", "women", "discover", "open day", "office visit", "networking",
               "webinar", "spotlight", "breakfast", "evening", "panel", "masterclass", "workshop",
               "challenge", "competition", "spring week", "fair", "session", "spring into", "spring insight",
               "immersion", "winternship"]
EXCLUDE_WORDS = ["apprentice", "apprenticeship", "year 12", "year 13", "sixth form", "school leaver",
                 "step in, step up", "career pathways", "high school", "secondary school",
                 "graduate programme", "graduate program", "summer analyst", "full time", "full-time",
                 "off-cycle internship", "industrial placement", "interest list", "recruiting news",
                 "summer internship", "summer intern", "placement year", "12-month", "full-time analyst",
                 "graduate scheme", "analyst program -", "associate program", "fellowship"]
CURRENT_YEAR = dt.date.today().year

CITIES = {
    # ville affichée : (zone, mots à chercher)
    "Paris": ("France", ["paris"]),
    "Londres": ("Royaume-Uni", ["london", "londres"]),
    "Glasgow": ("Royaume-Uni", ["glasgow"]),
    "Édimbourg": ("Royaume-Uni", ["edinburgh"]),
    "Chester": ("Royaume-Uni", ["chester"]),
    "Bournemouth": ("Royaume-Uni", ["bournemouth"]),
    "Sheffield": ("Royaume-Uni", ["sheffield"]),
    "Birmingham": ("Royaume-Uni", ["birmingham"]),
    "Leeds": ("Royaume-Uni", ["leeds"]),
    "Manchester": ("Royaume-Uni", ["manchester"]),
    "Belfast": ("Royaume-Uni", ["belfast"]),
    "Bristol": ("Royaume-Uni", ["bristol"]),
    "Francfort": ("Europe", ["frankfurt", "francfort"]),
    "Madrid": ("Europe", ["madrid"]),
    "Milan": ("Europe", ["milan"]),
    "Amsterdam": ("Europe", ["amsterdam"]),
    "Zurich": ("Europe", ["zurich", "zürich"]),
    "Dublin": ("Europe", ["dublin"]),
    "Luxembourg": ("Europe", ["luxembourg"]),
    "Munich": ("Europe", ["munich", "münchen"]),
    "Bruxelles": ("Europe", ["brussels", "bruxelles"]),
    "Genève": ("Europe", ["geneva", "genève"]),
    "Stockholm": ("Europe", ["stockholm"]),
    "New York": ("États-Unis", ["new york"]),
    "Hong Kong": ("Asie", ["hong kong"]),
    "Singapour": ("Asie", ["singapore", "singapour"]),
}
# Si la page d'un event contient un de ces mots, il s'adresse à des lycéens : on l'écarte.
PAGE_EXCLUDE_WORDS = ["year 13", "year 12", "sixth form", "a-level", "a level students", "school students",
                      "secondary school", "high school"]
VIRTUAL_WORDS = ["virtual", "zoom", "teams", "online", "webinar", "en ligne"]

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], start=1)}
# abréviations anglaises (Sep 28, 2026), placées après les noms complets pour que "march" passe avant "mar"
MONTHS.update({m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)})
MONTHS["sept"] = 9


# =========================================================
# Petites fonctions utiles
# =========================================================
def log(msg):
    print(msg, flush=True)


def get_page(url):
    """Télécharge une page web. Renvoie le HTML, ou None si ça échoue."""
    try:
        r = requests.get(url, headers=HEADERS_WEB, timeout=30)
        if r.status_code == 200:
            return r.text
        log(f"  ! {url} a répondu {r.status_code}")
    except requests.RequestException as e:
        log(f"  ! erreur réseau sur {url} : {e}")
    return None


def visible_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    return re.sub(r"\s+", " ", soup.get_text(" ")).strip()


def parse_date(text):
    """Trouve la première date dans un bout de texte. Comprend 15/12/2026, 15 December 2026, December 15th 2026."""
    t = text.lower()
    candidates = []
    m = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", t)                      # 15/12/2026 (format UK)
    if m:
        candidates.append((m.start(), (int(m.group(3)), int(m.group(2)), int(m.group(1)))))
    m = re.search(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(" + "|".join(MONTHS) + r")\s+(\d{4})", t)
    if m:
        candidates.append((m.start(), (int(m.group(3)), MONTHS[m.group(2)], int(m.group(1)))))
    m = re.search(r"\b(" + "|".join(MONTHS) + r")\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})", t)
    if m:
        candidates.append((m.start(), (int(m.group(3)), MONTHS[m.group(1)], int(m.group(2)))))
    for _, (y, mo, d) in sorted(candidates):
        try:
            return dt.date(y, mo, d).isoformat()
        except ValueError:
            continue
    return None


RANGE_SAME_MONTH = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s*(?:-|–|to)\s*\d{1,2}(?:st|nd|rd|th)?\s+(" + "|".join(MONTHS) + r")\s+(\d{4})")
RANGE_TWO_MONTHS = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(" + "|".join(MONTHS) + r")\s*(?:-|–|to)\s*\d{1,2}(?:st|nd|rd|th)?\s+(?:" + "|".join(MONTHS) + r")\s+(\d{4})")


def normalize_ranges(text):
    """Remplace '14th - 16th April 2027' par '14 April 2027' (on garde le 1er jour)."""
    t = RANGE_TWO_MONTHS.sub(lambda m: f"{m.group(1)} {m.group(2)} {m.group(3)}", text.lower())
    return RANGE_SAME_MONTH.sub(lambda m: f"{m.group(1)} {m.group(2)} {m.group(3)}", t)


def all_dates(text):
    """Toutes les dates trouvées dans un texte (format ISO), dans l'ordre."""
    t = text.lower()
    found = []
    pats = [
        (r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", lambda m: (int(m.group(3)), int(m.group(2)), int(m.group(1)))),
        (r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(" + "|".join(MONTHS) + r")\s+(\d{4})", lambda m: (int(m.group(3)), MONTHS[m.group(2)], int(m.group(1)))),
        (r"\b(" + "|".join(MONTHS) + r")\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})", lambda m: (int(m.group(3)), MONTHS[m.group(1)], int(m.group(2)))),
    ]
    for pat, conv in pats:
        for m in re.finditer(pat, t):
            try:
                y, mo, d = conv(m)
                found.append((m.start(), dt.date(y, mo, d).isoformat()))
            except ValueError:
                pass
    return [d for _, d in sorted(found)]


def date_after(label_regex, text, window=120):
    """Cherche une date juste après un mot-clé (ex : 'Event Date', 'Closing date')."""
    m = re.search(label_regex, text, flags=re.I)
    if not m:
        return None
    return parse_date(text[m.end(): m.end() + window])


def guess_kind(title, text):
    """'spring' pour une spring week / un programme d'insight de plusieurs jours, sinon 'event'."""
    t = title.lower()
    if any(w in t for w in ["spring", "insight week", "insight programme", "insight program", "insight 20",
                            "kickstarter", "immersion", "fttp", "discovery programme"]):
        return "spring"
    if re.search(r"\b(two|three|four|five|2|3|4|5)[- ]day (programme|program|insight|event)", text.lower()):
        return "spring"
    return "event"


def guess_type(title, text):
    s = (title + " " + text[:600]).lower()
    if any(w in s for w in ["women", "female", "femmes", "girls"]):
        return "Women in Finance"
    if any(w in s for w in ["challenge", "competition", "compétition"]):
        return "Compétition"
    if any(w in s for w in ["office visit", "open day", "open evening"]):
        return "Office visit"
    if any(w in s for w in ["insight", "discover", "spring week"]):
        return "Insight Day"
    if any(w in s for w in ["webinar", "virtual", "zoom", "online"]):
        return "Webinar"
    return "Networking"


def guess_place(title, text):
    """Renvoie (zone, ville). Regarde d'abord le titre, puis le début de la page."""
    for chunk in (title.lower(), text[:1500].lower()):
        for city, (zone, words) in CITIES.items():
            if any(w in chunk for w in words):
                return zone, city
        if any(w in chunk for w in VIRTUAL_WORDS):
            return "Virtuel", "En ligne"
    return "Autre", "À préciser"


def looks_like_event(title):
    t = title.lower()
    if any(w in t for w in EXCLUDE_WORDS):
        return False
    # annonces d'anciennes années (ex : "2025 Spring Insight") : on les ignore
    years = [int(y) for y in re.findall(r"\b(20\d\d)\b", t)]
    if years and max(years) < CURRENT_YEAR:
        return False
    return any(w in t for w in EVENT_WORDS)


STUDENT_WORDS = ["spring", "insight program", "insight day", "insight week", "insight event", "insight experience",
                 "insight evening", "insights event", "insight 20", "insight series", "discover", "women in", "immersion", "explore ", "open day", "taster",
                 "early insights", "virtual experience", "mentorship", "first year", "1st year", "winternship"]
JOB_WORDS = ["manager", "vice president", "director", "engineer", "banker", "associate", "analyst", "representative",
             "specialist", "lead ", "head of", "officer", "planner", "designer", "professional", "hiring event",
             "investor", "consultant", "developer", "advisor", "executive", "intern ", "internship"]


def looks_like_student_event(title):
    """Version stricte pour les sites qui mélangent offres d'emploi et programmes étudiants."""
    t = " " + title.lower() + " "
    if not looks_like_event(title):
        return False
    programme_words = ["spring", "insight program", "insight day", "insight week", "insight event", "early insights",
                       "insight 20", "kickstarter"]
    if any(w in t for w in JOB_WORDS) and not any(w in t for w in programme_words):
        return False
    return any(w in t for w in STUDENT_WORDS)


def build_item(src, event_id, url, title, text, extra_text=""):
    """Transforme une annonce (titre + texte de sa page) en ligne pour Supabase. None = à ignorer."""
    full = normalize_ranges((extra_text + " " + text).strip())
    low = full.lower()
    if any(w in low for w in PAGE_EXCLUDE_WORDS):
        log(f"  - ignoré (pour lycéens) : {title}")
        return None
    zone, city = guess_place(title, extra_text + " " + full)
    deadline = date_after(r"closing date|application deadline|deadline|apply by|applications close|applications will close|close on|closes on|window closes", full)
    event_start = date_after(r"event date|date of event|event will take place|takes place on|will take place from|programme dates|program dates", full)
    if event_start == deadline:
        event_start = None
    if not event_start:
        later = [d for d in all_dates(full) if (not deadline or d > deadline)]
        event_start = later[0] if later and deadline else (parse_date(title) or None)
    kind = guess_kind(title, full)
    typ = guess_type(title, full)
    return {
        "id": event_id, "firm": src["firm"], "title": title, "kind": kind,
        "type": "Spring Insight" if kind == "spring" and typ != "Women in Finance" else typ,
        "cat": src.get("cat"), "zone": zone, "city": city,
        "event_start": event_start, "deadline": deadline,
        "rolling": bool(re.search(r"rolling basis|on a rolling", full, re.I)),
        "elig": "Détecté automatiquement : vérifie l'éligibilité sur la page.",
        "url": url, "link_label": "S'inscrire", "source": src["id"],
    }


def log_item(it):
    log(f"  + NOUVEAU ({it['kind']}) : {it['title']} ({it['city']}, dates {it['event_start']}, deadline {it['deadline']})")


# =========================================================
# Supabase (base de données)
# =========================================================
def sb_headers(extra=None):
    h = {"apikey": SUPABASE_SECRET_KEY, "Content-Type": "application/json"}
    if extra:
        h.update(extra)
    return h


def sb_get(table, query):
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{table}?{query}", headers=sb_headers(), timeout=30)
    r.raise_for_status()
    return r.json()


def sb_upsert(table, rows):
    if not rows:
        return
    r = requests.post(f"{SUPABASE_URL}/rest/v1/{table}", headers=sb_headers(
        {"Prefer": "resolution=merge-duplicates,return=minimal"}), data=json.dumps(rows), timeout=30)
    if r.status_code >= 300:
        log(f"  ! Supabase a refusé l'écriture dans {table} : {r.status_code} {r.text[:300]}")
        r.raise_for_status()


# =========================================================
# Les 2 types de robots
# =========================================================
def scan_talnet(src, known_ids):
    """Liste tal.net : renvoie (nouveaux_events, ok)."""
    html = get_page(src["url"])
    if html is None:
        return [], False
    soup = BeautifulSoup(html, "html.parser")
    links = {}
    for a in soup.find_all("a", href=True):
        href = urljoin(src["url"], a["href"])
        title = re.sub(r"\s+", " ", a.get_text(" ")).strip()
        m = re.search(r"/opp/(\d+)", href)
        if m and title:
            # identifiant stable : site + numéro de l'annonce (évite les doublons si l'URL varie)
            host = re.sub(r"^https?://", "", href).split("/")[0]
            links[f"talnet:{host}:{m.group(1)}"] = (href.split("?")[0], title)
    log(f"  {len(links)} annonces trouvées sur la liste")
    if not links:
        log("  liste vide : aucun event publié pour l'instant (ou la page a changé de forme)")
        return [], True

    new_events = []
    for event_id, (url, title) in list(links.items()):
        if event_id in known_ids:
            continue
        if not looks_like_event(title):
            log(f"  - ignoré (pas un event) : {title}")
            continue
        if len(new_events) >= MAX_NEW_PAGES_PER_SOURCE:
            break
        time.sleep(1)             # on ne surcharge pas le site de la banque
        page = get_page(url)
        it = build_item(src, event_id, url, title, visible_text(page) if page else "")
        if it:
            new_events.append(it)
            log_item(it)
    return new_events, True


def _keep(title, event_id, known_ids, seen, accept_all=False):
    if event_id in known_ids or event_id in seen:
        return False
    if accept_all:
        years = [int(y) for y in re.findall(r"\b(20\d\d)\b", title)]
        if (years and max(years) < CURRENT_YEAR) or any(w in title.lower() for w in EXCLUDE_WORDS):
            return False
    elif not looks_like_student_event(title):
        return False
    seen.add(event_id)
    return True


def scan_workday(src, known_ids):
    """Site carrières Workday (ex : Blackstone, Houlihan Lokey). Utilise l'API JSON publique du site."""
    host, tenant, site = src["host"], src["tenant"], src["site"]
    api = f"https://{host}/wday/cxs/{tenant}/{site}"
    found, seen, ok = [], set(), False
    browser_ua = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/130.0 Safari/537.36")
    wd_headers = {"User-Agent": browser_ua, "Content-Type": "application/json", "Accept": "application/json",
                  "Accept-Language": "en-US", "Origin": f"https://{host}", "Referer": f"https://{host}/en-US/{site}"}
    sess = requests.Session()
    try:
        sess.get(f"https://{host}/en-US/{site}", headers={"User-Agent": browser_ua}, timeout=30)
    except requests.RequestException:
        pass
    for word in src.get("search", ["spring", "insight", "women", "discover"]):
        r = None
        for attempt in range(2):
            time.sleep(3 if attempt == 0 else 15)
            try:
                r = sess.post(f"{api}/jobs", timeout=30, headers=wd_headers,
                                  json={"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": word})
            except requests.RequestException as e:
                log(f"  ! erreur réseau : {e}"); r = None
            if r is not None and r.status_code != 429:
                break
        if r is None:
            continue
        if r.status_code != 200:
            log(f"  ! recherche '{word}' : {r.status_code}"); continue
        ok = True
        for j in r.json().get("jobPostings", []):
            path, title = j.get("externalPath", ""), (j.get("title") or "").strip()
            event_id = f"workday:{tenant}:{path.rsplit('_', 1)[-1]}"
            if not _keep(title, event_id, known_ids, seen):
                continue
            time.sleep(1)
            text = ""
            try:
                d = sess.get(f"{api}{path}", headers=wd_headers, timeout=30).json()
                text = visible_text(d.get("jobPostingInfo", {}).get("jobDescription", ""))
            except Exception:
                pass
            it = build_item(src, event_id, f"https://{host}/en-US/{site}{path}", title, text, j.get("locationsText", ""))
            if it:
                found.append(it); log_item(it)
    log(f"  {len(found)} nouveau(x) trouvé(s)")
    return found, ok


def scan_oracle(src, known_ids):
    """Site carrières Oracle Recruiting Cloud (ex : J.P. Morgan)."""
    host, site_nb = src["host"], src["site"]
    found, seen, ok = [], set(), False
    for word in src.get("search", ["spring", "insight", "women", "event"]):
        url = (f"https://{host}/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true"
               f"&expand=requisitionList&finder=findReqs;siteNumber={site_nb},limit=50,keyword=%22{word}%22")
        try:
            r = requests.get(url, headers=HEADERS_WEB, timeout=30)
        except requests.RequestException as e:
            log(f"  ! erreur réseau : {e}"); continue
        if r.status_code != 200:
            log(f"  ! recherche '{word}' : {r.status_code}"); continue
        ok = True
        items = r.json().get("items", [])
        reqs = items[0].get("requisitionList", []) if items else []
        for j in reqs:
            title, jid = (j.get("Title") or "").strip(), str(j.get("Id"))
            event_id = f"oracle:{host.split('.')[0]}:{jid}"
            if not _keep(title, event_id, known_ids, seen):
                continue
            text = " ".join(str(j.get(k) or "") for k in ("ShortDescriptionStr", "PrimaryLocation", "ExternalQualificationsStr"))
            loc = str(j.get("PrimaryLocation") or "")
            it = build_item(src, event_id, f"https://{host}/hcmUI/CandidateExperience/en/sites/{site_nb}/job/{jid}",
                            title, text, loc)
            if it:
                found.append(it); log_item(it)
    log(f"  {len(found)} nouveau(x) trouvé(s)")
    return found, ok


def scan_greenhouse(src, known_ids):
    """Tableau d'offres Greenhouse (sociétés de trading, hedge funds…). API publique officielle."""
    token = src["token"]
    r = None
    try:
        r = requests.get(f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true",
                         headers=HEADERS_WEB, timeout=30)
    except requests.RequestException as e:
        log(f"  ! erreur réseau : {e}")
    if r is None or r.status_code != 200:
        log(f"  ! Greenhouse '{token}' : {getattr(r, 'status_code', 'pas de réponse')}")
        return [], False
    import html as _html
    jobs = r.json().get("jobs", [])
    log(f"  {len(jobs)} offres sur le tableau")
    found, seen = [], set()
    for j in jobs:
        title, jid = (j.get("title") or "").strip(), str(j.get("id"))
        event_id = f"greenhouse:{token}:{jid}"
        if not _keep(title, event_id, known_ids, seen, src.get("accept_all", False)):
            continue
        text = visible_text(_html.unescape(j.get("content") or ""))
        loc = (j.get("location") or {}).get("name", "")
        it = build_item(src, event_id, j.get("absolute_url"), title, text, loc)
        if it and src.get("kind") and not re.search(r"visit day|insight day|open day", title, re.I):
            it["kind"] = src["kind"]
            if it["kind"] == "spring" and it["type"] != "Women in Finance":
                it["type"] = "Spring Insight"
        if it:
            found.append(it); log_item(it)
    log(f"  {len(found)} nouveau(x) trouvé(s)")
    return found, True


def scan_talentbrew(src, known_ids):
    """Sites carrières Radancy/TalentBrew (Barclays, Citi, BlackRock…) : ils chargent leurs résultats en JSON."""
    base = src["base"].rstrip("/")
    found, seen, ok = [], set(), False
    for word in src.get("search", ["spring", "insight"]):
        url = (f"{base}/search-jobs/results?ActiveFacetID=0&CurrentPage=1&RecordsPerPage=100&Distance=50"
               f"&RadiusUnitType=0&Keywords={word}&Location=&ShowRadius=False&IsPagination=False&CustomFacetName="
               f"&FacetTerm=&FacetType=0&SearchResultsModuleName=Search+Results&SearchFiltersModuleName=Search+Filters"
               f"&SortCriteria=0&SortDirection=0&SearchType=5")
        try:
            r = requests.get(url, headers={**HEADERS_WEB, "X-Requested-With": "XMLHttpRequest",
                                           "Accept": "application/json"}, timeout=30)
        except requests.RequestException as e:
            log(f"  ! erreur réseau : {e}"); continue
        if r.status_code != 200:
            log(f"  ! recherche '{word}' : {r.status_code}"); continue
        try:
            html_part = r.json().get("results", "")
        except ValueError:
            html_part = r.text
        ok = True
        soup = BeautifulSoup(html_part, "html.parser")
        for a in soup.find_all("a", href=True):
            if "/job/" not in a["href"]:
                continue
            head = a.find(["h2", "h3"])
            title = re.sub(r"\s+", " ", (head or a).get_text(" ")).strip()
            href = urljoin(base + "/", a["href"])
            event_id = "talentbrew:" + href
            if not _keep(title, event_id, known_ids, seen):
                continue
            time.sleep(1)
            page = get_page(href)
            it = build_item(src, event_id, href, title, visible_text(page) if page else "",
                            re.sub(r"\s+", " ", a.get_text(" ")))
            if it:
                found.append(it); log_item(it)
    log(f"  {len(found)} nouveau(x) trouvé(s)")
    return found, ok


def scan_links(src, known_ids):
    """Page carrières classique (ex : HSBC) : lit tous les liens qui ressemblent à un event ou une spring week,
    avec le texte autour (souvent les dates d'ouverture et de clôture)."""
    html = get_page(src["url"])
    if html is None:
        return [], False
    soup = BeautifulSoup(html, "html.parser")
    found, seen = [], set()
    for a in soup.find_all("a", href=True):
        head = a.find(["h2", "h3", "h4"])
        title = re.sub(r"\s+", " ", (head or a).get_text(" ")).replace("(opens in new window)", "").strip()
        title = re.split(r"\s+Location:", title)[0].strip()
        if len(title) < 12:
            continue
        href = urljoin(src["url"], a["href"]).split("#")[0]
        if src.get("href_contains") and src["href_contains"] not in href:
            continue
        event_id = "link:" + href
        if not _keep(title, event_id, known_ids, seen):
            continue
        # le bloc autour du lien contient souvent les dates (Opening Date, Closing Date, Start Date)
        block = a
        for _ in range(6):
            if block.parent is None or len(block.parent.get_text(" ")) > 2500:
                break
            block = block.parent
            if re.search(r"closing date|deadline|start date", block.get_text(" "), re.I):
                break
        context = re.sub(r"\s+", " ", block.get_text(" "))
        if src.get("follow"):
            time.sleep(1)
            page = get_page(href)
            context += " " + (visible_text(page) if page else "")
        it = build_item(src, event_id, href, title, context)
        if it:
            found.append(it); log_item(it)
    log(f"  {len(found)} nouveau(x) trouvé(s)")
    return found, True


def scan_page(src, state):
    """Page fixe : renvoie (a_change, ok, nouvelle_empreinte)."""
    html = get_page(src["url"])
    if html is None:
        return False, False, None
    text = visible_text(html)
    if len(text) < 200:
        return False, False, None
    digest = hashlib.sha256(text.encode()).hexdigest()
    old = (state or {}).get("last_hash")
    changed = old is not None and old != digest
    log("  la page a changé" if changed else "  pas de changement")
    return changed, True, digest


# =========================================================
# Mail
# =========================================================
def send_mail(subject, html_body):
    if not (RESEND_API_KEY and ALERT_EMAIL):
        log("  (pas de mail : RESEND_API_KEY ou ALERT_EMAIL manquant)")
        return
    r = requests.post("https://api.resend.com/emails", timeout=30,
                      headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
                      data=json.dumps({"from": "Events Tracker <onboarding@resend.dev>",
                                       "to": [ALERT_EMAIL], "subject": subject, "html": html_body}))
    log(f"  mail envoyé ({r.status_code})" if r.status_code < 300 else f"  ! mail refusé : {r.status_code} {r.text[:300]}")


def fmt_date(iso):
    if not iso:
        return "non publiée"
    d = dt.date.fromisoformat(iso[:10])
    return d.strftime("%d/%m/%Y")


def event_line(e):
    return (f"<li><b>{e['firm']}</b> — {e['title']} ({e.get('city') or ''})<br>"
            f"Event : {fmt_date(e.get('event_start'))} · Deadline : {fmt_date(e.get('deadline'))}"
            f"{' · au fil de l eau' if e.get('rolling') else ''}<br>"
            f"<a href=\"{e['url']}\">S'inscrire</a></li>")


# =========================================================
# Programme principal
# =========================================================
def main():
    sources = json.loads(Path(__file__).with_name("sources.json").read_text(encoding="utf-8"))["sources"]
    if ONLY:
        sources = [s for s in sources if s["id"] in ONLY.split(",")]
    if DRY_RUN:
        log("MODE TEST : rien ne sera écrit dans Supabase.")
        known_ids, states = set(), {}
    else:
        if not (SUPABASE_URL and SUPABASE_SECRET_KEY):
            log("ERREUR : SUPABASE_URL ou SUPABASE_SECRET_KEY manquant dans les Secrets GitHub.")
            sys.exit(1)
        known_ids = {row["id"] for row in sb_get("events", "select=id")}
        states = {row["source_id"]: row for row in sb_get("source_state", "select=*")}
    now = dt.datetime.now(dt.timezone.utc).isoformat()

    all_new, changed_pages, broken = [], [], []
    new_states = []

    for src in sources:
        log(f"\n== {src['id']} ({src['type']})")
        st = states.get(src["id"], {})
        digest = st.get("last_hash")
        if src["type"] in ("talnet", "workday", "oracle", "links", "greenhouse", "talentbrew"):
            scanner = {"talnet": scan_talnet, "workday": scan_workday, "oracle": scan_oracle,
                       "links": scan_links, "greenhouse": scan_greenhouse, "talentbrew": scan_talentbrew}[src["type"]]
            try:
                new, ok = scanner(src, known_ids)
            except Exception as e:          # une source qui plante ne doit pas bloquer les autres
                log(f"  ! erreur : {e}")
                new, ok = [], False
            new = [n for n in new if n["id"] not in {x["id"] for x in all_new}]
            all_new += new
        else:
            changed, ok, d = scan_page(src, st)
            if changed:
                changed_pages.append(src)
            digest = d or digest

        fails = 0 if ok else (st.get("fail_count") or 0) + 1
        if fails == 2:                       # on prévient une seule fois, au 2e échec d'affilée
            broken.append(src)
        new_states.append({"source_id": src["id"], "last_hash": digest, "fail_count": fails,
                           "last_ok": now if ok else st.get("last_ok")})

    if DRY_RUN:
        log(f"\nMODE TEST — {len(all_new)} annonce(s) seraient ajoutées.")
        return
    sb_upsert("events", all_new)
    sb_upsert("source_state", new_states)
    log(f"\nRésumé : {len(all_new)} nouvel(s) event(s), {len(changed_pages)} page(s) modifiée(s), {len(broken)} source(s) cassée(s)")

    # ---- Mail d'alerte (un seul par passage, seulement s'il y a du nouveau) ----
    parts = []
    if all_new:
        parts.append("<h3>Nouveaux events</h3><ul>" + "".join(event_line(e) for e in all_new) + "</ul>")
    if changed_pages:
        parts.append("<h3>Pages modifiées (va vérifier s'il y a un nouvel event)</h3><ul>" +
                     "".join(f"<li>{s['firm']} : <a href=\"{s['url']}\">{s['url']}</a></li>" for s in changed_pages) + "</ul>")
    if broken:
        parts.append("<h3>Sources cassées (le robot n'arrive plus à les lire)</h3><ul>" +
                     "".join(f"<li>{s['id']} : <a href=\"{s['url']}\">{s['url']}</a></li>" for s in broken) + "</ul>")
    if parts:
        n = len(all_new)
        subject = (f"{n} nouvel event" if n == 1 else f"{n} nouveaux events") if n else "Events Tracker : quelque chose a changé"
        footer = f"<p><a href=\"{SITE_URL}\">Ouvrir le tracker</a></p>" if SITE_URL else ""
        send_mail(subject, "".join(parts) + footer)

    # ---- Récap du lundi matin (passage entre 7h00 et 7h29 UTC) ----
    utc = dt.datetime.now(dt.timezone.utc)
    if (utc.weekday() == 0 and utc.hour == 7 and utc.minute < 30) or os.environ.get("FORCE_DIGEST") == "1":
        today = dt.date.today()
        soon = (today + dt.timedelta(days=14)).isoformat()
        rows = sb_get("events", f"select=*&active=is.true&deadline=gte.{today.isoformat()}&deadline=lte.{soon}&order=deadline.asc")
        if rows:
            send_mail(f"Récap : {len(rows)} deadline(s) dans les 14 prochains jours",
                      "<h3>Deadlines à venir</h3><ul>" + "".join(event_line(e) for e in rows) + "</ul>")


if __name__ == "__main__":
    main()
