# 🏔️ MILAREPA — Converse avec Milarepa

> Un LLM conversationnel qui permet de dialoguer avec Jetsun Milarepa (1052-1135),
> le yogi-poète tibétain, comme s'il était assis en face de toi dans sa grotte de montagne.

## 🎯 Concept

Élodie pose une question → le système trouve les passages les plus pertinents dans les 1 400 pages d'écrits de Milarepa → Claude répond avec la voix, le style et la sagesse de Milarepa, en s'appuyant sur ses vrais textes.

## 🏗️ Architecture (RAG - Retrieval Augmented Generation)

```
Question d'Élodie
       ↓
[1] Embedding de la question (API Voyage/OpenAI)
       ↓
[2] Recherche vectorielle dans Supabase (pgvector)
    → trouve les 4-5 passages les plus pertinents
       ↓
[3] Prompt système (personnalité Milarepa)
    + passages trouvés + question
       ↓
[4] API Claude → Réponse comme Milarepa
       ↓
Interface web magnifique
```

## 📁 Structure du projet

```
milarippa/
├── README.md                    ← Ce fichier
├── requirements.txt             ← Dépendances Python
├── .env.example                 ← Variables d'environnement (template)
├── config/
│   └── milarepa_prompt.md       ← Le prompt système (l'âme de Milarepa)
├── data/
│   ├── raw/                     ← PDFs originaux (copier ici)
│   ├── processed/               ← Textes extraits (.txt)
│   └── chunks/                  ← Chunks découpés (.jsonl)
├── scripts/
│   ├── 01_extract_text.py       ← Extraction texte des PDFs
│   ├── 02_chunk_texts.py        ← Découpage intelligent
│   ├── 03_generate_embeddings.py ← Génération des vecteurs
│   ├── 04_upload_to_supabase.py ← Upload dans la base vectorielle
│   └── setup_supabase.sql       ← Script SQL pour créer la table
└── app/
    ├── main.py                  ← Serveur Flask
    ├── rag.py                   ← Logique RAG (search + generate)
    ├── templates/
    │   └── index.html           ← Interface de chat
    └── static/
        ├── css/
        │   └── style.css
        └── js/
            └── chat.js
```

## 🚀 Setup rapide

### 1. Environnement
```bash
cd milarippa
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 2. Variables d'environnement
```bash
cp .env.example .env
# Éditer .env avec tes clés API
```

### 3. Pipeline de données (dans l'ordre !)
```bash
# Copier les PDFs dans data/raw/
python scripts/01_extract_text.py
python scripts/02_chunk_texts.py
python scripts/03_generate_embeddings.py
python scripts/04_upload_to_supabase.py
```

### 4. Lancer l'app
```bash
python app/main.py
# → http://localhost:5000
```

## 🔑 APIs nécessaires

- **Anthropic (Claude)** : Pour la génération des réponses → https://console.anthropic.com/
- **OpenAI ou Voyage AI** : Pour les embeddings → https://platform.openai.com/ ou https://www.voyageai.com/
- **Supabase** : Pour la base vectorielle → https://supabase.com/

## 📚 Corpus (1 439 pages)

| Document | Pages | Langue |
|---|---|---|
| Hundred Thousand Songs (Garma Chang) | 752 | EN |
| Le Poète Tibétain (Jacques Bacot) | 303 | FR |
| The Life of Milarepa (Lhalungpa) | 240 | EN |
| Sixty Songs (Chang) | 141 | EN |
| Wikiquote Milarepa | 3 | EN |
