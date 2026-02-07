"""
MILARIPPA - Logique RAG
=======================
1. Reçoit une question
2. Génère l'embedding de la question
3. Cherche les passages les plus proches dans Supabase
4. Envoie le tout à Claude avec le prompt Milarepa
5. Retourne la réponse
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client
import anthropic

load_dotenv()

# Clients API
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Config
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
PROMPT_PATH = Path("config/milarepa_prompt.md")
NUM_RESULTS = 5  # Nombre de passages à récupérer


def load_system_prompt() -> str:
    """Charge le prompt système de Milarepa."""
    return PROMPT_PATH.read_text(encoding="utf-8")


def get_query_embedding(query: str) -> list[float]:
    """Génère l'embedding d'une question."""
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=query,
    )
    return response.data[0].embedding


def search_similar_chunks(query_embedding: list[float], num_results: int = NUM_RESULTS) -> list[dict]:
    """Cherche les chunks les plus similaires dans Supabase."""
    result = supabase.rpc("search_milarepa", {
        "query_embedding": query_embedding,
        "match_count": num_results,
        "match_threshold": 0.3,
    }).execute()

    return result.data


def format_context(chunks: list[dict]) -> str:
    """Formate les chunks trouvés en contexte lisible pour Claude."""
    if not chunks:
        return "(Aucun passage pertinent trouvé dans les écrits)"

    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get("source", "Inconnu")
        section = chunk.get("section", "")
        chunk_type = chunk.get("type", "")
        similarity = chunk.get("similarity", 0)
        texte = chunk.get("texte", "")

        context_parts.append(
            f"[Passage {i}] (Source: {source} | {section} | Type: {chunk_type} | Pertinence: {similarity:.0%})\n{texte}"
        )

    return "\n\n---\n\n".join(context_parts)


def generate_response(question: str, conversation_history: list[dict] = None) -> dict:
    """
    Pipeline RAG complet :
    Question → Embedding → Recherche → Claude → Réponse
    """
    # 1. Embedding de la question
    query_embedding = get_query_embedding(question)

    # 2. Recherche des passages pertinents
    chunks = search_similar_chunks(query_embedding)

    # 3. Calculer le score de similarité moyen
    avg_similarity = 0.0
    if chunks:
        avg_similarity = sum(c.get("similarity", 0) for c in chunks) / len(chunks)

    # 4. Construire le prompt avec le contexte
    system_prompt = load_system_prompt()
    context = format_context(chunks)
    system_prompt = system_prompt.replace("{context}", context)
    system_prompt = system_prompt.replace("{avg_similarity}", str(avg_similarity))

    # 5. Construire les messages (avec historique si disponible)
    messages = []
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": question})

    # 6. Appel à Claude
    response = claude_client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        system=system_prompt,
        messages=messages,
    )

    answer = response.content[0].text

    return {
        "answer": answer,
        "sources": [
            {
                "source": c.get("source"),
                "section": c.get("section"),
                "type": c.get("type"),
                "similarity": round(c.get("similarity", 0), 3),
            }
            for c in chunks
        ],
    }
