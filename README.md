# STATO Live

Collecte automatique des données PMU pour l'application STATO.

## Contenu de ce dossier (3 fichiers seulement)

| Fichier | Rôle |
|---------|------|
| `fetch_pmu.py` | Script Python de collecte |
| `fetch-pmu.yml` | Configuration automatique (GitHub Actions) |
| `live.json` | Données du jour (mis à jour automatiquement) |

## Installation étape par étape

### 1. Créer un compte GitHub
Allez sur https://github.com → Sign up → créez un compte gratuit.

### 2. Créer un dépôt
- Cliquez le **+** en haut à droite → **New repository**
- Nom : `stato-live`
- Cochez **Public**
- Cliquez **Create repository**

### 3. Uploader les fichiers
Sur la page de votre dépôt vide :
- Cliquez **"uploading an existing file"**
- **Glissez-déposez les 3 fichiers** de ce dossier (fetch_pmu.py, fetch-pmu.yml, live.json)
- Cliquez **Commit changes**

### 4. Créer le dossier .github/workflows
Ce dossier spécial est obligatoire pour GitHub Actions.
- Sur votre dépôt, cliquez **Add file → Create new file**
- Dans le champ "Name your file", tapez exactement : `.github/workflows/fetch-pmu.yml`
  (GitHub crée les dossiers automatiquement quand vous tapez le `/`)
- Dans la zone de contenu, **copiez-collez tout le contenu** du fichier `fetch-pmu.yml`
- Cliquez **Commit changes**
- Vous pouvez maintenant **supprimer** le fichier `fetch-pmu.yml` à la racine

### 5. Activer GitHub Pages
- Allez dans **Settings** (onglet en haut de votre dépôt)
- Menu gauche → **Pages**
- Source : **Deploy from a branch**
- Branch : **main** / Folder : **/ (root)**
- Cliquez **Save**

### 6. Récupérer votre URL
Attendez 2 minutes, puis votre URL sera :
```
https://VOTRE_NOM.github.io/stato-live/live.json
```

### 7. Connecter à STATO
Dans STATO v1.7, onglet **En direct**, collez cette URL et cliquez **Connecter**.

## Mise à jour automatique

Le script tourne automatiquement à **8h00** et **11h00** chaque matin (heure de Paris).
Pour lancer manuellement : onglet **Actions** → **Collecte données PMU** → **Run workflow**.
