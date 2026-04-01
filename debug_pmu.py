#!/usr/bin/env python3
"""
STATO Debug — Affiche tous les champs disponibles pour un partant PMU
Tourne une seule fois manuellement pour identifier les vrais noms de champs
"""

import json, urllib.request, urllib.error, time, sys, os
from datetime import datetime, timedelta

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, */*',
    'Accept-Language': 'fr-FR,fr;q=0.9',
    'Referer': 'https://www.pmu.fr/',
}

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
            print(f"  Erreur: {e}")
            time.sleep(2 ** i)
    return None

def main():
    now = datetime.now()
    today = now.strftime('%d%m%Y')

    print("=" * 60)
    print(f"STATO Debug — {now.strftime('%d/%m/%Y %H:%M')}")
    print("=" * 60)

    # 1. Récupérer le programme du jour
    url_prog = f"https://offline.turfinfo.api.pmu.fr/rest/client/7/programme/{today}?specialisation=INTERNET"
    print(f"\nRécupération du programme: {url_prog}")
    data = fetch(url_prog)

    if not data:
        print("ERREUR: Programme inaccessible")
        sys.exit(1)

    reunions = data.get('programme', {}).get('reunions', [])
    print(f"Réunions trouvées: {len(reunions)}")

    if not reunions:
        print("ERREUR: Aucune réunion aujourd'hui")
        sys.exit(1)

    # Prendre la première réunion, première course
    r = reunions[0]
    hippo = r.get('hippodrome', {}).get('libelle', '?')
    num_r = r.get('numOfficiel', 1)
    courses = r.get('courses', [])

    if not courses:
        print("ERREUR: Aucune course")
        sys.exit(1)

    c = courses[0]
    num_c = c.get('numOrdre', 1)

    print(f"\nCourse testée: R{num_r}C{num_c} — {hippo} — {c.get('libelle','?')}")

    # 2. Récupérer les participants via offline (même endpoint que le script principal)
    url_p = f"https://offline.turfinfo.api.pmu.fr/rest/client/7/programme/{today}/R{num_r}/C{num_c}/participants?specialisation=INTERNET"
    print(f"\nEndpoint offline: {url_p}")
    p_data = fetch(url_p)

    if p_data:
        participants = p_data.get('participants', [])
        print(f"Participants trouvés (offline): {len(participants)}")
        if participants:
            p = participants[0]
            print(f"\n{'='*60}")
            print(f"CHAMPS DISPONIBLES (offline) pour: {p.get('nom','?')}")
            print(f"{'='*60}")
            for key, val in sorted(p.items()):
                # Afficher la valeur tronquée si trop longue
                val_str = str(val)
                if len(val_str) > 80:
                    val_str = val_str[:80] + '...'
                print(f"  {key:35s} = {val_str}")
    else:
        print("Endpoint offline: pas de réponse")

    # 3. Essayer aussi via online (client 61)
    print(f"\n{'='*60}")
    url_p2 = f"https://online.turfinfo.api.pmu.fr/rest/client/61/programme/{today}/R{num_r}/C{num_c}/participants?specialisation=INTERNET"
    print(f"Endpoint online: {url_p2}")
    p_data2 = fetch(url_p2)

    if p_data2:
        participants2 = p_data2.get('participants', [])
        print(f"Participants trouvés (online): {len(participants2)}")
        if participants2:
            p2 = participants2[0]
            print(f"\n{'='*60}")
            print(f"CHAMPS DISPONIBLES (online) pour: {p2.get('nom','?')}")
            print(f"{'='*60}")
            for key, val in sorted(p2.items()):
                val_str = str(val)
                if len(val_str) > 80:
                    val_str = val_str[:80] + '...'
                print(f"  {key:35s} = {val_str}")

            # Chercher spécifiquement les champs liés aux cotes
            print(f"\n{'='*60}")
            print("CHAMPS LIÉS AUX COTES:")
            print(f"{'='*60}")
            cote_keys = [k for k in p2.keys() if any(x in k.lower() for x in
                ['cote', 'rapport', 'direct', 'proba', 'enjeu', 'mise', 'odd'])]
            for k in cote_keys:
                print(f"  {k:35s} = {p2[k]}")

            # Chercher les champs liés à la musique/performances
            print(f"\n{'='*60}")
            print("CHAMPS LIÉS À LA MUSIQUE/PERFORMANCES:")
            print(f"{'='*60}")
            perf_keys = [k for k in p2.keys() if any(x in k.lower() for x in
                ['music', 'perf', 'cours', 'dernier', 'histo', 'form'])]
            for k in perf_keys:
                val_str = str(p2[k])
                if len(val_str) > 120:
                    val_str = val_str[:120] + '...'
                print(f"  {k:35s} = {val_str}")
    else:
        print("Endpoint online: pas de réponse")

    # 4. Sauvegarder le JSON brut du premier partant pour analyse
    debug_output = {
        'date': today,
        'hippo': hippo,
        'reunion': num_r,
        'course': num_c,
        'offline_premier_partant': participants[0] if p_data and p_data.get('participants') else None,
        'online_premier_partant': p_data2.get('participants', [None])[0] if p_data2 else None,
    }

    with open('debug_partant.json', 'w', encoding='utf-8') as f:
        json.dump(debug_output, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print("Fichier debug_partant.json sauvegardé")
    print("Consultez les logs ci-dessus pour identifier les vrais noms de champs")
    sys.exit(0)

if __name__ == '__main__':
    main()
