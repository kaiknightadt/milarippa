"""
MILAREPA - Étape 1 : Extraction du texte des PDFs
===================================================
Lit chaque PDF dans data/raw/ et produit un fichier .txt propre dans data/processed/
"""

import os
import re
import fitz  # pymupdf
from pathlib import Path

# Chemins
RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def clean_text(text: str) -> str:
    """Nettoie le texte extrait d'un PDF."""
    # Supprime les multiples espaces
    text = re.sub(r' {2,}', ' ', text)
    # Supprime les multiples sauts de ligne (garde max 2)
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Supprime les numéros de page isolés
    text = re.sub(r'\n\s*\d{1,3}\s*\n', '\n', text)
    # Supprime les headers/footers répétitifs (à adapter selon les PDFs)
    text = re.sub(r'(?i)the hundred thousand songs of milarepa\s*\n', '', text)
    # Nettoie les tirets de césure en fin de ligne
    text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)
    return text.strip()


def extract_pdf(pdf_path: Path) -> str:
    """Extrait le texte d'un PDF avec PyMuPDF."""
    doc = fitz.open(pdf_path)
    full_text = []

    for page_num, page in enumerate(doc):
        text = page.get_text()
        if text.strip():
            full_text.append(f"\n--- PAGE {page_num + 1} ---\n{text}")

    doc.close()
    return clean_text("\n".join(full_text))


def main():
    pdf_files = list(RAW_DIR.glob("*.pdf"))

    if not pdf_files:
        print(f"❌ Aucun PDF trouvé dans {RAW_DIR}/")
        print(f"   Copie tes PDFs dans le dossier {RAW_DIR}/ d'abord !")
        return

    print(f"📚 {len(pdf_files)} PDF(s) trouvé(s)\n")

    for pdf_path in pdf_files:
        print(f"📖 Extraction de {pdf_path.name}...")
        text = extract_pdf(pdf_path)

        output_path = PROCESSED_DIR / f"{pdf_path.stem}.txt"
        output_path.write_text(text, encoding="utf-8")

        # Stats
        word_count = len(text.split())
        print(f"   ✅ {word_count:,} mots → {output_path}\n")

    print("🎉 Extraction terminée !")


if __name__ == "__main__":
    main()
