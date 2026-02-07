# 🚀 MILARIPPA - Deployment Guide

## Déploiement sur Render.com

### 1. Créer un compte Render
- Aller sur https://render.com/
- Créer un compte gratuit

### 2. Connecter ton repo GitHub
- Lier ton dépôt GitHub à Render
- S'assurer que le fichier `render.yaml` est à la racine du projet

### 3. Déployer
```bash
git push origin main
```

Render détectera le `render.yaml` et lancera automatiquement le déploiement.

### 4. Configurer les variables d'environnement
Dans le dashboard Render :
1. Aller à **Dashboard** → **milarippa** → **Environment**
2. Ajouter :
   - `ANTHROPIC_API_KEY=sk-ant-...`
   - `OPENAI_API_KEY=sk-proj-...`
   - `SUPABASE_URL=https://xxxxx.supabase.co`
   - `SUPABASE_KEY=eyJ...` (clé service role)

### 5. Attendre le déploiement
- Vérifier les logs : **Dashboard** → **milarippa** → **Logs**
- Accéder à l'app : **https://milarippa.onrender.com**

---

## Upgrades Réalisés

### ✅ 1. Historique des Conversations
- ✅ Tables Supabase : `conversations` + `messages`
- ✅ Sidebar avec liste des dialogues passés
- ✅ Bouton "Nouveau dialogue"
- ✅ Rechargement automatique au clic
- ✅ Suppression de conversations
- ✅ Persistance des messages

### ✅ 2. Préparation Déploiement
- ✅ Dockerfile optimisé
- ✅ render.yaml configuré
- ✅ .dockerignore pour build rapide
- ✅ App écoute sur `0.0.0.0:PORT`
- ✅ PORT depuis variable d'environnement

---

## Architecture Finale

```
milarippa/
├── app/
│   ├── main.py              ← Flask + endpoints historique
│   ├── rag.py              ← Logique RAG (inchangé)
│   ├── templates/
│   │   └── index.html      ← UI avec sidebar
│   └── static/
│       ├── css/style.css   ← Styles sidebar
│       └── js/chat.js      ← Gestion conversations
├── config/                 ← Prompt système
├── scripts/                ← Pipeline de données
├── Dockerfile              ← Image Docker
├── render.yaml             ← Config Render
├── .dockerignore           ← Exclusions Docker
├── requirements.txt
├── .env                    ← Variables (local)
└── .env.example           ← Template
```

---

## Troubleshooting Render

### Build fails
```bash
# Vérifier les logs
# Dashboard → Logs → View build log

# Erreur commune : Port mal configuré
# ✅ main.py écoute sur 0.0.0.0:PORT ✓
```

### App not accessible
- ✅ Vérifier que les variables d'env sont bien configurées
- ✅ Vérifier les logs pour les erreurs Supabase
- ✅ S'assurer que le domaine Render est correct

### Problèmes Supabase
- ✅ Vérifier que la clé est une **clé service role** (pas publishable)
- ✅ Vérifier que la table `conversations` existe
- ✅ Vérifier les permissions RLS (doit être disabled)

---

## Local Testing

```bash
# Avec Docker
docker build -t milarippa .
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  -e OPENAI_API_KEY=sk-proj-... \
  -e SUPABASE_URL=https://... \
  -e SUPABASE_KEY=eyJ... \
  milarippa

# Sans Docker
.\venv\Scripts\Activate.ps1
python app/main.py
# → http://localhost:5000
```

---

## Notes

- 🏔️ L'app écoute sur **0.0.0.0** (accessible en production)
- 📦 Le port est configurable via `PORT` (défaut: 5000)
- 🔐 Les clés API sont en variables d'environnement
- 💾 L'historique est persistant (Supabase)
- ⚡ Render gratuit suffit pour démarrer
