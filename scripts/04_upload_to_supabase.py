"""
MILARIPPA - Étape 4 : Upload vers Supabase
===========================================
Envoie tous les chunks avec leurs embeddings dans la base vectorielle Supabase.
⚠️ Avant de lancer ce script, exécuter setup_supabase.sql dans le SQL Editor de Supabase !
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
from tqdm import tqdm

load_dotenv()

# Config
CHUNKS_FILE = Path("data/chunks/milarepa_chunks_with_embeddings.jsonl")
BATCH_SIZE = 50  # Supabase accepte des inserts en batch

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)


def main():
    if not CHUNKS_FILE.exists():
        print(f"❌ Fichier non trouvé : {CHUNKS_FILE}")
        print("   Lance d'abord : python scripts/03_generate_embeddings.py")
        return

    # Charger les chunks
    chunks = []
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            chunks.append(json.loads(line))

    print(f"📤 Upload de {len(chunks)} chunks vers Supabase...\n")

    # Upload par batches
    success = 0
    errors = 0

    for i in tqdm(range(0, len(chunks), BATCH_SIZE), desc="Upload"):
        batch = chunks[i:i + BATCH_SIZE]

        # Préparer les données (format Supabase)
        rows = []
        for chunk in batch:
            rows.append({
                "id": chunk["id"],
                "source": chunk["source"],
                "langue": chunk["langue"],
                "section": chunk.get("section", ""),
                "type": chunk.get("type", "enseignement"),
                "texte": chunk["texte"],
                "tokens": chunk.get("tokens", 0),
                "embedding": chunk["embedding"],
            })

        try:
            result = supabase.table("milarepa_chunks").upsert(rows).execute()
            success += len(batch)
        except Exception as e:
            print(f"\n❌ Erreur batch {i}: {e}")
            errors += len(batch)

    print(f"\n{'='*50}")
    print(f"🎉 UPLOAD TERMINÉ")
    print(f"   ✅ Succès : {success}")
    print(f"   ❌ Erreurs : {errors}")

    # Vérification
    count = supabase.table("milarepa_chunks").select("id", count="exact").execute()
    print(f"   📊 Total en base : {count.count} chunks")


if __name__ == "__main__":
    main()
