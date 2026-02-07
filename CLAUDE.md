# CLAUDE.md — Instructions pour Claude Code

## Contexte du projet
MILAREPA est un chatbot RAG (Retrieval Augmented Generation) qui permet de converser
avec Jetsun Milarepa, le yogi-poète tibétain du XIe siècle. L'utilisateur pose des questions
et reçoit des réponses dans le style poétique et spirituel de Milarepa, basées sur ses
écrits authentiques (1 400+ pages de corpus).

## Stack technique
- **Backend** : Python / Flask
- **LLM** : API Anthropic (Claude)
- **Embeddings** : API OpenAI (text-embedding-3-small)
- **Base vectorielle** : Supabase (PostgreSQL + pgvector)
- **Frontend** : HTML/CSS/JS vanilla (pas de framework)

## Structure
- `scripts/` : Pipeline de données (extraction → chunking → embeddings → upload)
- `app/` : Application web (Flask + interface de chat)
- `config/` : Prompt système de Milarepa
- `data/` : PDFs sources, textes extraits, chunks

## Pipeline de données (ordre d'exécution)
1. `scripts/01_extract_text.py` — Extraction texte des PDFs
2. `scripts/02_chunk_texts.py` — Découpage intelligent en chunks
3. `scripts/03_generate_embeddings.py` — Génération des vecteurs
4. `scripts/04_upload_to_supabase.py` — Upload dans Supabase

## Points d'attention
- Le corpus est bilingue (FR + EN) — les embeddings gèrent le multilingue
- Le prompt système dans `config/milarepa_prompt.md` est crucial pour la qualité
- Les PDFs sources incluent un OCR ancien (Bacot, 1925) qui peut avoir des artefacts
- L'interface doit rester sobre, spirituelle, élégante (thème sombre, or, serif pour Milarepa)

## Commandes utiles
```bash
# Lancer l'app
cd app && python main.py

# Relancer le pipeline complet
python scripts/01_extract_text.py
python scripts/02_chunk_texts.py
python scripts/03_generate_embeddings.py
python scripts/04_upload_to_supabase.py
```

## Ce projet est un cadeau pour Élodie 🎁
C'est un projet personnel et passionnel. La qualité de l'expérience conversationnelle
est prioritaire sur tout le reste. Milarepa doit sonner VRAI — poétique, profond,
ancré dans l'expérience, jamais robotique.
