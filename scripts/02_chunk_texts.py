"""
MILARIPPA - Étape 2 : Découpage intelligent (Chunking)
======================================================
Découpe les textes extraits en chunks sémantiquement cohérents.
Stratégie : on découpe par sections/chapitres d'abord, puis on subdivise
les sections trop longues avec un overlap pour garder le contexte.
"""

import json
import re
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

import tiktoken

# Config
PROCESSED_DIR = Path("data/processed")
CHUNKS_DIR = Path("data/chunks")
CHUNKS_DIR.mkdir(parents=True, exist_ok=True)

MAX_TOKENS = 800      # Taille max d'un chunk en tokens
OVERLAP_TOKENS = 100   # Chevauchement entre chunks
MIN_TOKENS = 50        # Taille min (éviter les micro-chunks)

# Tokenizer pour compter les tokens
enc = tiktoken.get_encoding("cl100k_base")


@dataclass
class Chunk:
    id: str
    source: str          # Nom du document source
    langue: str          # "fr" ou "en"
    section: str         # Chapitre/section identifié
    type: str            # "chant", "recit", "enseignement", "dialogue", "biographie"
    texte: str           # Le contenu
    tokens: int          # Nombre de tokens
    page_debut: Optional[int] = None


# === DÉTECTION DES SOURCES ===

SOURCE_CONFIG = {
    "Le_poete_tibétain": {"langue": "fr", "nom": "Le Poète Tibétain (Bacot)"},
    "Le_poete_tibetain": {"langue": "fr", "nom": "Le Poète Tibétain (Bacot)"},
    "Garma_C_C__Chang": {"langue": "en", "nom": "Hundred Thousand Songs (Chang)"},
    "The-Life-of-Milarepa": {"langue": "en", "nom": "The Life of Milarepa (Lhalungpa)"},
    "wh095_Chang_Sixty": {"langue": "en", "nom": "Sixty Songs (Chang)"},
    "Milarepa_-_Wikiquote": {"langue": "en", "nom": "Wikiquote Milarepa"},
    "Le_livre_tibetain_de_la_vie_et_de_la_mort": {"langue": "fr", "nom": "Le Livre Tibétain de la Vie et de la Mort (Sogyal Rinpoché)"},
    "Padmasambhava_-_Advice_From_the_Lotus_Born": {"langue": "en", "nom": "Advice From the Lotus Born (Padmasambhava)"},
    "padmasambhava_la_clef_du_sens_profond": {"langue": "fr", "nom": "La Clef du Sens Profond (Padmasambhava)"},
}


def get_source_config(filename: str) -> dict:
    """Identifie la source à partir du nom de fichier."""
    for key, config in SOURCE_CONFIG.items():
        if key in filename:
            return config
    return {"langue": "en", "nom": filename}


def count_tokens(text: str) -> int:
    return len(enc.encode(text))


# === DÉCOUPAGE PAR SECTIONS ===

def split_by_sections(text: str) -> list[tuple[str, str]]:
    """
    Découpe un texte en sections basées sur les marqueurs structurels.
    Retourne une liste de (titre_section, contenu).
    """
    # Patterns de découpage (chapitres, stories, chants, pages)
    section_patterns = [
        r'\n(?:CHAPTER|Chapter|STORY|Story|PART|Part)\s+[\dIVXLCDM]+[.\s:].*?\n',
        r'\n(?:CHANT|Song|SONG)\s+[\dIVXLCDM]+[.\s:].*?\n',
        r'\n--- PAGE \d+ ---\n',
    ]

    # Essayer chaque pattern, du plus structuré au moins
    for pattern in section_patterns:
        splits = re.split(pattern, text)
        headers = re.findall(pattern, text)

        if len(splits) > 3:  # Au moins quelques sections trouvées
            sections = []
            for i, content in enumerate(splits):
                if content.strip():
                    header = headers[i - 1].strip() if i > 0 and i - 1 < len(headers) else "Introduction"
                    sections.append((header, content.strip()))
            return sections

    # Fallback : découper par doubles sauts de ligne (paragraphes)
    paragraphs = text.split('\n\n')
    sections = []
    current = []
    current_title = "Section 1"
    section_num = 1

    for para in paragraphs:
        current.append(para)
        if count_tokens('\n\n'.join(current)) > MAX_TOKENS:
            sections.append((current_title, '\n\n'.join(current[:-1])))
            current = [para]
            section_num += 1
            current_title = f"Section {section_num}"

    if current:
        sections.append((current_title, '\n\n'.join(current)))

    return sections


def detect_chunk_type(text: str, source_name: str) -> str:
    """Détecte le type de contenu d'un chunk."""
    text_lower = text.lower()

    # Indices de chant/poésie (lignes courtes, structure en vers)
    lines = text.strip().split('\n')
    short_lines = sum(1 for l in lines if 0 < len(l.strip()) < 60)
    if short_lines > len(lines) * 0.6 and len(lines) > 4:
        return "chant"

    if any(word in text_lower for word in ["milarepa sang", "milarepa chanta", "il chanta", "he sang", "then sang"]):
        return "chant"

    if any(word in text_lower for word in ["dit à", "répondit", "demanda", "said to", "replied", "asked"]):
        return "dialogue"

    if "Life" in source_name or "Poète" in source_name or "biograph" in source_name.lower():
        return "biographie"

    return "enseignement"


# === SUBDIVISION DES CHUNKS TROP LONGS ===

def subdivide_chunk(text: str, max_tokens: int = MAX_TOKENS, overlap: int = OVERLAP_TOKENS) -> list[str]:
    """Subdivise un texte trop long en chunks avec overlap (simple version)."""
    text_tokens = enc.encode(text)
    
    if len(text_tokens) <= max_tokens:
        return [text]

    chunks = []
    
    # Découper par paragraphes d'abord
    paragraphs = text.split('\n\n')
    current_chunk = []
    current_tokens = 0
    
    for para in paragraphs:
        para_tokens = len(enc.encode(para))
        
        if current_tokens + para_tokens > max_tokens and current_chunk:
            # Sauvegarder le chunk actuel
            chunk_text = '\n\n'.join(current_chunk).strip()
            if chunk_text:
                chunks.append(chunk_text)
            # Réinitialiser avec overlap (prendre dernier para)
            current_chunk = [current_chunk[-1] if current_chunk else '', para]
            current_tokens = para_tokens + len(enc.encode(current_chunk[0]))
        else:
            current_chunk.append(para)
            current_tokens += para_tokens
    
    # Ajouter le dernier chunk
    if current_chunk:
        chunk_text = '\n\n'.join(current_chunk).strip()
        if chunk_text:
            chunks.append(chunk_text)
    
    return chunks


# === PIPELINE PRINCIPAL ===

def process_file(txt_path: Path) -> list[Chunk]:
    """Traite un fichier texte complet et retourne des chunks."""
    config = get_source_config(txt_path.stem)
    text = txt_path.read_text(encoding="utf-8")
    chunks = []
    chunk_id = 0

    print(f"  📐 Découpage en sections...")
    sections = split_by_sections(text)
    print(f"  📄 {len(sections)} sections trouvées")

    for section_title, section_content in sections:
        if count_tokens(section_content) < MIN_TOKENS:
            continue

        # Subdiviser si trop long
        sub_texts = subdivide_chunk(section_content)

        for sub_text in sub_texts:
            if count_tokens(sub_text) < MIN_TOKENS:
                continue

            chunk = Chunk(
                id=f"{txt_path.stem}_{chunk_id:04d}",
                source=config["nom"],
                langue=config["langue"],
                section=section_title[:100],
                type=detect_chunk_type(sub_text, config["nom"]),
                texte=sub_text,
                tokens=count_tokens(sub_text),
            )
            chunks.append(chunk)
            chunk_id += 1

    return chunks


def main():
    txt_files = list(PROCESSED_DIR.glob("*.txt"))

    if not txt_files:
        print(f"❌ Aucun fichier .txt dans {PROCESSED_DIR}/")
        print("   Lance d'abord : python scripts/01_extract_text.py")
        return

    # Charger les chunks existants pour identifier les fichiers déjà traités
    output_path = CHUNKS_DIR / "milarepa_chunks.jsonl"
    processed_sources = set()

    if output_path.exists():
        with open(output_path, "r", encoding="utf-8") as f:
            for line in f:
                chunk = json.loads(line)
                # Extraire le nom du fichier source de l'ID (format: filename_0000)
                source_file = "_".join(chunk["id"].split("_")[:-1])
                processed_sources.add(source_file)
        print(f"📋 {len(processed_sources)} fichier(s) déjà traité(s)")

    # Filtrer pour ne traiter que les nouveaux fichiers
    new_txt_files = [f for f in txt_files if f.stem not in processed_sources]

    if not new_txt_files:
        print(f"✅ Tous les fichiers .txt ont déjà été chunkés ({len(txt_files)} fichiers)")
        print(f"   Aucun nouveau fichier à traiter.")
        return

    print(f"📚 {len(txt_files)} fichier(s) .txt trouvé(s)")
    print(f"📚 {len(new_txt_files)} nouveau(x) fichier(s) à chunker\n")

    all_chunks = []

    for txt_path in new_txt_files:
        print(f"\n📖 Traitement de {txt_path.name}...")
        chunks = process_file(txt_path)
        all_chunks.extend(chunks)
        print(f"  ✅ {len(chunks)} chunks créés")

    # Sauvegarder en mode APPEND (ajouter aux chunks existants)
    mode = "a" if output_path.exists() else "w"
    with open(output_path, mode, encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(asdict(chunk), ensure_ascii=False) + "\n")

    # Stats
    total_tokens = sum(c.tokens for c in all_chunks)
    types = {}
    for c in all_chunks:
        types[c.type] = types.get(c.type, 0) + 1

    print(f"\n{'='*50}")
    print(f"🎉 CHUNKING TERMINÉ")
    print(f"   Nouveaux chunks : {len(all_chunks)}")
    print(f"   Total tokens    : {total_tokens:,}")
    print(f"   Moyenne/chunk   : {total_tokens // len(all_chunks)} tokens")
    print(f"   Types : {types}")
    print(f"   Fichier : {output_path}")
    print(f"   Mode : {'APPEND (ajout)' if mode == 'a' else 'NOUVEAU'}")


if __name__ == "__main__":
    main()
