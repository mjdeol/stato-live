#!/usr/bin/env python3
"""
STATO Live — Collecteur de données PMU
Tourne chaque jour sur GitHub Actions (8h et 11h Paris).
Récupère le programme du jour + arrivées de la veille.
Publie : live.json (lu par STATO directement via GitHub Pages)
"""

import json, urllib.request, urllib.error, time, sys, os
from datetime import datetime, timedelta

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, */*',
    'Accept-Language': 'fr-FR,fr;q=0.9',
    'Referer': 'https://www.pmu.fr/',
}
BASE = "https://offline.turfinfo.api.pmu.fr/rest/client/7/programme/{date}"
BASE_PART = "https://online.turfinfo.api.pmu.fr/rest/client/61/programme/{date}/{r}/{c}/participants?specialisation=INTERNET"

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

def fetch_programme(date_str):
    print(f"Programme {date_str}")
    data = fetch(BASE.format(date=date_str) + "?specialisation=INTERNET")
    if not data: return []
    reunions_raw = data.get('programme', {}).get('reunions', [])
    print(f"  {len(reunions_raw)} réunion(s)")
    reunions = []
    for r in reunions_raw:
        hippo = r.get('hippodrome', {}).get('libelle', '') or r.get('libelle', '')
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
            p_data = fetch(BASE_PART.format(date=date_str, r=f"R{num_r}", c=f"C{num_c}"))
            if p_data:
                for p in p_data.get('participants', []):
                    if p.get('statut') == 'NON_PARTANT': continue
                    cote = p.get('coteProbable') or p.get('rapport')
                    course['participants'].append({
                        'num': p.get('numPmu') or p.get('numero'),
                        'nom': p.get('nom', '?'),
                        'driver': p.get('driver') or p.get('jockey', ''),
                        'cote': round(float(cote), 1) if cote else None,
                        'favori': bool(p.get('favori')),
                    })
            courses.append(course)
        reunions.append({'num': num_r, 'hippo': hippo, 'courses': courses})
    return reunions

def fetch_arrivees(date_str):
    print(f"Arrivées {date_str}")
    data = fetch(BASE.format(date=date_str) + "?specialisation=INTERNET")
    if not data: return []
    arrivees = []
    for r in data.get('programme', {}).get('reunions', []):
        hippo = r.get('hippodrome', {}).get('libelle', '') or r.get('libelle', '')
        num_r = r.get('numOfficiel', 0)
        for c in r.get('courses', []):
            num_c = c.get('numOrdre', 0)
            time.sleep(0.2)
            p_data = fetch(f"https://offline.turfinfo.api.pmu.fr/rest/client/7/programme/{date_str}/R{num_r}/C{num_c}/participants?specialisation=INTERNET")
            if not p_data: continue
            arrived = [(p.get('ordreArrivee', 99), p.get('numPmu') or p.get('numero'))
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
    print(f"  {len(arrivees)} arrivée(s)")
    return arrivees

def main():
    now = datetime.now()
    today = now.strftime('%d%m%Y')
    yesterday = (now - timedelta(days=1)).strftime('%d%m%Y')

    programme = fetch_programme(today)
    arrivees = fetch_arrivees(yesterday)

    output = {
        'generated_at': now.isoformat(),
        'date_today': f"{today[:2]}/{today[2:4]}/{today[4:]}",
        'date_yesterday': f"{yesterday[:2]}/{yesterday[2:4]}/{yesterday[4:]}",
        'programme': programme or [],
        'arrivees_veille': arrivees,
        'status': 'ok' if programme else 'partial',
    }

    with open('live.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"live.json généré ({len(json.dumps(output))//1024} KB)")
    sys.exit(0)

if __name__ == '__main__':
    main()
