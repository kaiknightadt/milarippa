"""
MILARIPPA - Étape 3 : Génération des Embeddings
================================================
Transforme chaque chunk de texte en vecteur numérique (embedding).
Ces vecteurs capturent le SENS du texte, pas juste les mots.
Utilise l'API OpenAI (text-embedding-3-small) par défaut.
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm

load_dotenv()

# Config
CHUNKS_DIR = Path("data/chunks")
INPUT_FILE = CHUNKS_DIR / "milarepa_chunks.jsonl"
OUTPUT_FILE = CHUNKS_DIR / "milarepa_chunks_with_embeddings.jsonl"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
BATCH_SIZE = 50  # Nombre de chunks par requête API (max ~2048 pour OpenAI)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Génère les embeddings pour une liste de textes."""
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]


def main():
    if not INPUT_FILE.exists():
        print(f"❌ Fichier non trouvé : {INPUT_FILE}")
        print("   Lance d'abord : python scripts/02_chunk_texts.py")
        return

    # Charger tous les chunks
    all_chunks = []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            all_chunks.append(json.loads(line))

    # Charger les chunks qui ont déjà des embeddings
    processed_chunk_ids = set()
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                chunk = json.loads(line)
                processed_chunk_ids.add(chunk["id"])
        print(f"📋 {len(processed_chunk_ids)} chunk(s) déjà vectorisé(s)")

    # Filtrer pour ne traiter que les nouveaux chunks
    chunks = [c for c in all_chunks if c["id"] not in processed_chunk_ids]

    if not chunks:
        print(f"✅ Tous les chunks ont déjà des embeddings ({len(all_chunks)} chunks)")
        print(f"   Aucun nouveau chunk à vectoriser.")
        return

    print(f"📊 {len(all_chunks)} chunks au total")
    print(f"📊 {len(chunks)} nouveau(x) chunk(s) à vectoriser")
    print(f"🤖 Modèle : {EMBEDDING_MODEL}")
    print(f"📦 Batch size : {BATCH_SIZE}\n")

    # Traiter par batches
    all_results = []
    for i in tqdm(range(0, len(chunks), BATCH_SIZE), desc="Embedding"):
        batch = chunks[i:i + BATCH_SIZE]
        texts = [chunk["texte"] for chunk in batch]

        try:
            embeddings = get_embeddings(texts)

            for chunk, embedding in zip(batch, embeddings):
                chunk["embedding"] = embedding
                all_results.append(chunk)

        except Exception as e:
            print(f"\n❌ Erreur batch {i}: {e}")
            # On continue avec les suivants
            continue

    # Sauvegarder en mode APPEND
    mode = "a" if OUTPUT_FILE.exists() else "w"
    with open(OUTPUT_FILE, mode, encoding="utf-8") as f:
        for chunk in all_results:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    print(f"\n{'='*50}")
    print(f"🎉 EMBEDDINGS GÉNÉRÉS")
    print(f"   Nouveaux chunks : {len(all_results)}/{len(chunks)}")
    print(f"   Dimension vecteur : {len(all_results[0]['embedding']) if all_results else 'N/A'}")
    print(f"   Fichier : {OUTPUT_FILE}")
    print(f"   Mode : {'APPEND (ajout)' if mode == 'a' else 'NOUVEAU'}")

    # Estimation du coût (text-embedding-3-small = $0.02 / 1M tokens)
    total_tokens = sum(c.get("tokens", 0) for c in all_results)
    cost = (total_tokens / 1_000_000) * 0.02
    print(f"   💰 Coût estimé : ${cost:.4f}")


if __name__ == "__main__":
    main()
