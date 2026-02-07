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

    # Charger tous les chunks
    all_chunks = []
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            all_chunks.append(json.loads(line))

    print(f"📋 {len(all_chunks)} chunks chargés depuis le fichier")

    # Récupérer les IDs déjà présents dans Supabase
    print(f"🔍 Vérification des chunks déjà présents dans Supabase...")
    try:
        existing_chunks = supabase.table("milarepa_chunks").select("id").execute()
        existing_ids = {chunk["id"] for chunk in existing_chunks.data}
        print(f"📊 {len(existing_ids)} chunk(s) déjà en base")
    except Exception as e:
        print(f"⚠️ Erreur lors de la récupération des IDs : {e}")
        print(f"   Tentative d'upload de tous les chunks...")
        existing_ids = set()

    # Filtrer pour ne uploader que les nouveaux chunks
    chunks = [c for c in all_chunks if c["id"] not in existing_ids]

    if not chunks:
        print(f"✅ Tous les chunks sont déjà dans Supabase ({len(all_chunks)} chunks)")
        print(f"   Aucun nouveau chunk à uploader.")
        return

    print(f"📤 Upload de {len(chunks)} nouveau(x) chunk(s) vers Supabase...\n")

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
    print(f"   ✅ Nouveaux chunks uploadés : {success}")
    print(f"   ❌ Erreurs : {errors}")

    # Vérification
    count = supabase.table("milarepa_chunks").select("id", count="exact").execute()
    print(f"   📊 Total en base : {count.count} chunks")


if __name__ == "__main__":
    main()
