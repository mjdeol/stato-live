#!/usr/bin/env python3
"""
STATO Live — Collecteur de données PMU v2.1
Champs documentés depuis debug_partant.json du 01/04/2026
"""

import json, urllib.request, urllib.error, time, sys, os
from datetime import datetime, timedelta

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, */*',
    'Accept-Language': 'fr-FR,fr;q=0.9',
    'Referer': 'https://www.pmu.fr/',
}

BASE_PROG = "https://offline.turfinfo.api.pmu.fr/rest/client/7/programme/{date}?specialisation=INTERNET"
BASE_PART = "https://offline.turfinfo.api.pmu.fr/rest/client/7/programme/{date}/R{r}/C{c}/participants?specialisation=INTERNET"

# Mapping noms API PMU → noms base STATO
HIPPO_MAP = {
    "PARIS-VINCENNES": "Vincennes", "VINCENNES": "Vincennes",
    "AUTEUIL": "Auteuil", "PARIS-AUTEUIL": "Auteuil",
    "PARIS-LONGCHAMP": "Paris-Longchamp", "LONGCHAMP": "Paris-Longchamp",
    "DEAUVILLE": "Deauville", "DEAUVILLE-LA TOUQUES": "Deauville",
    "CHANTILLY": "Chantilly",
    "SAINT-CLOUD": "Saint Cloud", "SAINT CLOUD": "Saint Cloud",
    "CAGNES-SUR-MER": "Cagnes Sur Mer", "CAGNES SUR MER": "Cagnes Sur Mer",
    "ENGHIEN-SOISY": "Enghien Soisy", "ENGHIEN SOISY": "Enghien Soisy",
    "ENGHIEN": "Enghien",
    "MAISONS-LAFFITTE": "Maisons Laffitte", "MAISONS LAFFITTE": "Maisons Laffitte",
    "COMPIEGNE": "Compiegne", "COMPIEGNE": "Compiegne",
    "CABOURG": "Cabourg", "CLAIREFONTAINE": "Clairefontaine",
    "VICHY": "Vichy", "PAU": "Pau", "FONTAINEBLEAU": "Fontainebleau",
    "CAEN": "Caen", "LAVAL": "Laval",
    "LYON-PARILLY": "Lyon Parilly", "LYON PARILLY": "Lyon Parilly",
    "MARSEILLE-BORELY": "Marseille Borely", "MARSEILLE BORELY": "Marseille Borely",
    "ANGERS": "Angers", "CRAON": "Craon", "NANTES": "Nantes",
    "TOULOUSE": "Toulouse", "DIEPPE": "Dieppe",
}

def norm_hippo(raw):
    """Normalise le nom d'hippodrome API vers le nom DB STATO."""
    if not raw: return raw
    raw = raw.strip()
    # Essai direct
    if raw in HIPPO_MAP: return HIPPO_MAP[raw]
    # Essai majuscules
    up = raw.upper()
    if up in HIPPO_MAP: return HIPPO_MAP[up]
    # Essai partiel : chercher si un nom DB est contenu
    for api_key, db_val in HIPPO_MAP.items():
        if api_key in up or up in api_key:
            return db_val
    # Fallback : title case
    return raw.title()

def fetch(url, retries=3):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code in (403, 404): return None
            time.sleep(2 ** i)
        except Exception as e:
            print(f"  Erreur {type(e).__name__}: {e}")
            time.sleep(2 ** i)
    return None

def norm_type(t):
    if not t: return None
    t = str(t).strip().lower()
    if 'attel' in t: return 'Attelé'
    if 'mont' in t: return 'Monté'
    if 'plat' in t: return 'Plat'
    if 'haies' in t: return 'Haies'
    if 'steeple' in t: return 'Steeple Chase'
    return None

def extraire_hippo(r):
    """Extrait le nom de l'hippodrome depuis la réunion — essaie plusieurs champs."""
    hippo_obj = r.get('hippodrome') or {}
    raw = (hippo_obj.get('libelle') or hippo_obj.get('libelleLong') or
           hippo_obj.get('libelleCourt') or hippo_obj.get('nom') or
           r.get('libelle') or r.get('libelleLong') or '')
    result = norm_hippo(raw)
    if result:
        print(f"    Hippodrome: '{raw}' → '{result}'")
    return result

def extraire_partant(p):
    if p.get('statut') == 'NON_PARTANT': return None
    drd = p.get('dernierRapportDirect') or {}
    drr = p.get('dernierRapportReference') or {}
    cote_directe   = drd.get('rapport')
    cote_ouverture = drr.get('rapport')
    tendance = drr.get('indicateurTendance', '=')
    favori   = drd.get('favoris', False)
    gains = p.get('gainsParticipant') or {}
    oeil_raw = p.get('oeilleres', '')
    if oeil_raw == 'SANS_OEILLERES': oeilleres = None
    elif 'AUSTRALIENNES' in oeil_raw: oeilleres = 'australiennes'
    elif oeil_raw: oeilleres = 'oui'
    else: oeilleres = None
    def_raw = p.get('deferre', '')
    if not def_raw or def_raw == 'FERRE': deferre = None
    elif 'ANTERIEURS_POSTERIEURS' in def_raw: deferre = '4 membres'
    elif 'ANTERIEURS' in def_raw: deferre = 'antérieurs'
    elif 'POSTERIEURS' in def_raw: deferre = 'postérieurs'
    else: deferre = 'oui'
    avis_map = {'POSITIF': '+', 'NEGATIF': '-', 'NEUTRE': '=', 'TRES_POSITIF': '++'}
    return {
        'num':            p.get('numPmu'),
        'nom':            p.get('nom', '?'),
        'driver':         p.get('driver', ''),
        'entraineur':     p.get('entraineur', ''),
        'age':            p.get('age'),
        'sexe':           p.get('sexe', ''),
        'robe':           (p.get('robe') or {}).get('libelleCourt', ''),
        'cote':           round(float(cote_directe), 1) if cote_directe else None,
        'coteOuverture':  round(float(cote_ouverture), 1) if cote_ouverture else None,
        'coteTendance':   tendance,
        'favori':         favori,
        'musique':        p.get('musique', ''),
        'nbCourses':      p.get('nombreCourses', 0),
        'nbVictoires':    p.get('nombreVictoires', 0),
        'nbPlaces':       p.get('nombrePlaces', 0),
        'gainsCarriere':  (gains.get('gainsCarriere') or 0) // 100,
        'gainsAnnee':     (gains.get('gainsAnneeEnCours') or 0) // 100,
        'oeilleres':      oeilleres,
        'deferre':        deferre,
        'avisEntraineur': avis_map.get(p.get('avisEntraineur', 'NEUTRE'), '='),
        'driverChange':   p.get('driverChange', False),
        'indicateurInedit': p.get('indicateurInedit', False),
        'handicapDistance': p.get('handicapDistance'),
    }

def fetch_programme(date_str):
    print(f"Programme {date_str}")
    data = fetch(BASE_PROG.format(date=date_str))
    if not data: return []
    reunions_raw = data.get('programme', {}).get('reunions', [])
    print(f"  {len(reunions_raw)} reunion(s)")
    reunions = []
    for r in reunions_raw:
        hippo = extraire_hippo(r)
        num_r = r.get('numOfficiel', 0)
        courses = []
        for c in r.get('courses', []):
            num_c = c.get('numOrdre', 0)
            heure_ts = c.get('heureDepart')
            heure = ''
            if heure_ts:
                try: heure = datetime.fromtimestamp(heure_ts/1000).strftime('%H:%M')
                except: pass
            course = {
                'num': num_c, 'libelle': c.get('libelle', f'C{num_c}'),
                'heure': heure, 'distance': c.get('distance'),
                'type': norm_type(c.get('specialite') or c.get('discipline')),
                'partants': c.get('nombrePartants', 0),
                'isTQQ': c.get('categorieParticipant') == 'TIERCE_QUARTE_QUINTE',
                'participants': [],
            }
            time.sleep(0.3)
            p_data = fetch(BASE_PART.format(date=date_str, r=num_r, c=num_c))
            if p_data:
                for p in p_data.get('participants', []):
                    partant = extraire_partant(p)
                    if partant: course['participants'].append(partant)
                nb = len(course['participants'])
                nb_cotes = sum(1 for p in course['participants'] if p['cote'])
                print(f"    C{num_c} {nb} partants | {nb_cotes} cotes")
            courses.append(course)
        hippo_raw = (r.get('hippodrome') or {}).get('libelle','') or r.get('libelle','')
        reunions.append({'num': num_r, 'hippo': hippo, 'hippo_raw': hippo_raw, 'courses': courses})
    return reunions

def fetch_arrivees(date_str):
    print(f"Arrivees {date_str}")
    data = fetch(BASE_PROG.format(date=date_str))
    if not data: return []
    arrivees = []
    for r in data.get('programme', {}).get('reunions', []):
        hippo = extraire_hippo(r)
        num_r = r.get('numOfficiel', 0)
        for c in r.get('courses', []):
            num_c = c.get('numOrdre', 0)
            time.sleep(0.2)
            p_data = fetch(BASE_PART.format(date=date_str, r=num_r, c=num_c))
            if not p_data: continue
            arrived = [(p.get('ordreArrivee', 99), p.get('numPmu'))
                       for p in p_data.get('participants', [])
                       if p.get('ordreArrivee') and p.get('ordreArrivee') < 99]
            arrived.sort()
            nums = [n for _, n in arrived[:5]]
            if nums:
                arrivees.append({
                    'date': f"{date_str[:2]}/{date_str[2:4]}/{date_str[4:]}",
                    'lieu': hippo, 'rc': f"R{num_r}C{num_c}",
                    'type': norm_type(c.get('specialite')),
                    'distance': c.get('distance'),
                    'libelle': c.get('libelle', ''),
                    'arrivee': nums,
                })
    print(f"  {len(arrivees)} arrivee(s)")
    return arrivees

def main():
    now = datetime.now()
    today = now.strftime('%d%m%Y')
    yesterday = (now - timedelta(days=1)).strftime('%d%m%Y')
    print(f"STATO Live v2.1 — {now.strftime('%d/%m/%Y %H:%M')}")
    programme  = fetch_programme(today)
    arrivees   = fetch_arrivees(yesterday)
    total_part  = sum(len(c['participants']) for r in programme for c in r['courses'])
    total_cotes = sum(1 for r in programme for c in r['courses'] for p in c['participants'] if p['cote'])
    # Résumé des hippodromes pour vérification du mapping
    hippos_debug = [{'brut': r.get('hippo_raw','?'), 'normalise': r.get('hippo','?')} 
                    for r in programme]

    output = {
        'generated_at':   now.isoformat(),
        'date_today':     f"{today[:2]}/{today[2:4]}/{today[4:]}",
        'date_yesterday': f"{yesterday[:2]}/{yesterday[2:4]}/{yesterday[4:]}",
        'programme':      programme or [],
        'arrivees_veille': arrivees,
        'status':         'ok' if programme else 'partial',
        'stats':          {'reunions': len(programme), 'partants': total_part, 'avec_cotes': total_cotes},
        'hippos':         hippos_debug,
    }
    with open('live.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, separators=(',', ':'))
    kb = os.path.getsize('live.json') // 1024
    print(f"OK — live.json {kb} KB | {len(programme)} reunions | {total_part} partants | {total_cotes} cotes")
    sys.exit(0)

if __name__ == '__main__':
    main()
