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

    # Charger les chunks
    chunks = []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            chunks.append(json.loads(line))

    print(f"📊 {len(chunks)} chunks à vectoriser")
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

    # Sauvegarder
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for chunk in all_results:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    print(f"\n{'='*50}")
    print(f"🎉 EMBEDDINGS GÉNÉRÉS")
    print(f"   Chunks traités : {len(all_results)}/{len(chunks)}")
    print(f"   Dimension vecteur : {len(all_results[0]['embedding'])}")
    print(f"   Fichier : {OUTPUT_FILE}")

    # Estimation du coût (text-embedding-3-small = $0.02 / 1M tokens)
    total_tokens = sum(c.get("tokens", 0) for c in all_results)
    cost = (total_tokens / 1_000_000) * 0.02
    print(f"   💰 Coût estimé : ${cost:.4f}")


if __name__ == "__main__":
    main()
