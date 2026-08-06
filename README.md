# RENOV'ISOL

**Outil d'aide à la décision pour l'isolation thermique par l'intérieur des bâtiments anciens**

Développé dans le cadre d'un projet de fin d'études du Mastère Spécialisé Expert en Construction et Habitat Durables (Arts et Métiers, 2025-2026).

---

## Installation locale

### 1. Cloner le dépôt

```bash
git clone https://github.com/VOTRE_NOM/renov-isol.git
cd renov-isol
```

### 2. Créer un environnement virtuel

```bash
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configurer les secrets

Copiez le template et remplissez-le :

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Remplissez le fichier avec :
- votre mot de passe administrateur
- l'identifiant de votre Google Sheet
- les clés de votre compte de service Google

### 5. Lancer l'application

```bash
streamlit run app.py
```

L'application s'ouvre automatiquement sur `http://localhost:8501`.

---

## Configuration Google Sheets (étape obligatoire)

### 1. Créer un projet Google Cloud

1. Allez sur [console.cloud.google.com](https://console.cloud.google.com)
2. Cliquez sur **Nouveau projet** → nommez-le (ex. : `renov-isol`)
3. Sélectionnez le projet

### 2. Activer les APIs

Dans le menu **APIs et services → Bibliothèque**, activez :
- **Google Sheets API**
- **Google Drive API**

### 3. Créer un compte de service

1. **APIs et services → Identifiants → Créer des identifiants → Compte de service**
2. Nommez-le (ex. : `renov-isol-sheets`)
3. Rôle : **Éditeur**
4. Cliquez sur le compte créé → **Clés → Ajouter une clé → JSON**
5. Téléchargez le fichier JSON

### 4. Créer le Google Sheet

1. Allez sur [sheets.google.com](https://sheets.google.com)
2. Créez un nouveau classeur nommé **RENOV-ISOL**
3. Créez deux onglets : `materiaux` et `analyses`
4. **Partagez le Sheet** avec l'email du compte de service (du type `xxx@xxx.iam.gserviceaccount.com`) en lui donnant le rôle **Éditeur**
5. Copiez l'ID du Sheet depuis l'URL : `docs.google.com/spreadsheets/d/**IDENTIFIANT**/edit`

### 5. Remplir secrets.toml

Copiez les valeurs du fichier JSON dans `.streamlit/secrets.toml`.

---

## Déploiement sur Streamlit Community Cloud

### 1. Créer le dépôt GitHub

```bash
git init
git add .
git commit -m "Initial commit — RENOV'ISOL"
git branch -M main
git remote add origin https://github.com/VOTRE_NOM/renov-isol.git
git push -u origin main
```

> ⚠️ Vérifiez que `.streamlit/secrets.toml` est bien dans `.gitignore` avant de pousser.

### 2. Connecter à Streamlit Community Cloud

1. Allez sur [share.streamlit.io](https://share.streamlit.io)
2. Connectez-vous avec GitHub
3. Cliquez **New app**
4. Sélectionnez votre dépôt, la branche `main`, le fichier `app.py`
5. Cliquez **Deploy**

### 3. Configurer les secrets sur Streamlit Cloud

1. Dans votre app déployée → **⋮ → Settings → Secrets**
2. Copiez-collez le contenu de votre `secrets.toml` local
3. Sauvegardez — l'app redémarre automatiquement

Vous obtenez une URL publique du type :
```
https://renov-isol-xxxx.streamlit.app
```

### 4. Mettre à jour l'application

```bash
git add .
git commit -m "Mise à jour"
git push
```

Streamlit redéploie automatiquement.

---

## Générer un QR code pour la soutenance

1. Récupérez votre URL publique (ex. : `https://renov-isol.streamlit.app`)
2. Allez sur [qr-code-generator.com](https://www.qr-code-generator.com) (gratuit)
3. Collez l'URL → générez → téléchargez en PNG haute résolution

---

## Architecture du projet

```
RENOV-ISOL/
├── app.py                    # Accueil Streamlit
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/
│   └── secrets.toml          # NE PAS COMMITTER
├── database/
│   └── sheets.py             # Connexion Google Sheets
├── modules/
│   ├── calculations.py       # Calculs thermiques et économiques
│   ├── decision.py           # Filtrage et recommandations
│   ├── hygro.py              # Compatibilité hygrothermique
│   ├── pdf_export.py         # Génération PDF
│   └── utils.py
├── pages/
│   ├── 2_Nouvelle_analyse.py
│   ├── 3_Resultats.py
│   ├── 4_Base_materiaux.py
│   ├── 5_Administration.py
│   ├── 6_Methode.py
│   └── 7_A_propos.py
└── tests/
    └── test_calculations.py
```

---

## Lancer les tests

```bash
python tests/test_calculations.py
```

---

## Limites

Cet outil est une aide à la décision. Il ne remplace pas une simulation thermique dynamique, une étude hygrothermique détaillée ou une expertise du bâtiment.
