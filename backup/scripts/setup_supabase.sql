-- =============================================
-- MILARIPPA - Setup Supabase (pgvector)
-- =============================================
-- Exécuter ce SQL dans l'éditeur SQL de Supabase
-- Dashboard → SQL Editor → New Query

-- 1. Activer l'extension pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Créer la table des chunks
CREATE TABLE IF NOT EXISTS milarepa_chunks (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,           -- Nom du document source
    langue TEXT NOT NULL,            -- "fr" ou "en"
    section TEXT,                    -- Chapitre/section
    type TEXT,                       -- "chant", "recit", "enseignement", "dialogue", "biographie"
    texte TEXT NOT NULL,             -- Le contenu textuel
    tokens INTEGER,                  -- Nombre de tokens
    embedding VECTOR(1536),          -- Vecteur d'embedding (1536 dim pour text-embedding-3-small)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Créer l'index pour la recherche vectorielle rapide
-- (IVFFlat est plus rapide que la recherche exacte pour les gros datasets)
CREATE INDEX IF NOT EXISTS milarepa_chunks_embedding_idx
ON milarepa_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 50);

-- 4. Créer la fonction de recherche sémantique
CREATE OR REPLACE FUNCTION search_milarepa(
    query_embedding VECTOR(1536),
    match_count INT DEFAULT 5,
    match_threshold FLOAT DEFAULT 0.3
)
RETURNS TABLE (
    id TEXT,
    source TEXT,
    langue TEXT,
    section TEXT,
    type TEXT,
    texte TEXT,
    tokens INTEGER,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        mc.id,
        mc.source,
        mc.langue,
        mc.section,
        mc.type,
        mc.texte,
        mc.tokens,
        1 - (mc.embedding <=> query_embedding) AS similarity
    FROM milarepa_chunks mc
    WHERE 1 - (mc.embedding <=> query_embedding) > match_threshold
    ORDER BY mc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- 5. Créer la table des conversations
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,          -- Titre auto-généré (première question tronquée)
    user_id TEXT NOT NULL,        -- Identifiant utilisateur (IP Hash ou device ID)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. Créer la table des messages
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL,           -- "user" ou "assistant"
    content TEXT NOT NULL,        -- Le message
    sources TEXT,                 -- JSON array des sources citées
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. Index pour recherche rapide
CREATE INDEX IF NOT EXISTS conversations_user_id_idx ON conversations(user_id);
CREATE INDEX IF NOT EXISTS messages_conversation_id_idx ON messages(conversation_id);

-- 8. Vérification
-- SELECT COUNT(*) FROM milarepa_chunks;
-- SELECT * FROM conversations LIMIT 10;
