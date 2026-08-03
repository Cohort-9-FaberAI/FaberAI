-- Migration: 02_dfm_reference_docs_vector_search
-- Enables pgvector on the existing (empty) dfm_reference_docs table, pins the
-- embedding column to the dimension produced by BAAI/bge-base-en-v1.5 (768),
-- adds a similarity index, and exposes a similarity-search RPC the backend
-- calls from app/services/dfm_knowledge/retrieval.py.
--
-- Safe to run once against the table shown in the Supabase schema editor:
--   dfm_reference_docs(id uuid, source text, doc_version text,
--     section_ref text, content_type text, content text, table_data jsonb,
--     page_no int4, embedding vector, created_at timestamptz)

CREATE EXTENSION IF NOT EXISTS vector;

-- Pin the embedding column to a fixed dimension. If the table's "embedding"
-- column was created with a bare `vector` type (no dimension), this fails
-- until the column is empty — which it is, since ingestion hasn't run yet.
ALTER TABLE public.dfm_reference_docs
    ALTER COLUMN embedding TYPE vector(768);

-- created_at should default itself; the table as shown didn't set a default.
ALTER TABLE public.dfm_reference_docs
    ALTER COLUMN created_at SET DEFAULT now();

-- ivfflat needs a rough row-count estimate for `lists`; 100 is a reasonable
-- default for a few thousand chunks (one ASME standard). Re-tune (roughly
-- sqrt(row_count)) if more standards get ingested later.
CREATE INDEX IF NOT EXISTS dfm_reference_docs_embedding_idx
    ON public.dfm_reference_docs
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Cheap filters the agent/UI will want alongside similarity search.
CREATE INDEX IF NOT EXISTS dfm_reference_docs_source_idx
    ON public.dfm_reference_docs (source);
CREATE INDEX IF NOT EXISTS dfm_reference_docs_section_ref_idx
    ON public.dfm_reference_docs (section_ref);

ALTER TABLE public.dfm_reference_docs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "rls_policy_all"
ON public.dfm_reference_docs
AS PERMISSIVE
FOR ALL
TO public
USING (true)
WITH CHECK (true);

-- Cosine-similarity search, called via supabase.rpc("match_dfm_reference_docs", ...).
-- Returns the row plus a 0-1 similarity score (1 = identical direction).
CREATE OR REPLACE FUNCTION match_dfm_reference_docs(
    query_embedding vector(768),
    match_count int DEFAULT 5,
    min_similarity float DEFAULT 0.3,
    filter_source text DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    source text,
    doc_version text,
    section_ref text,
    content_type text,
    content text,
    table_data jsonb,
    page_no int4,
    similarity float
)
LANGUAGE sql STABLE
AS $$
    SELECT
        d.id,
        d.source,
        d.doc_version,
        d.section_ref,
        d.content_type,
        d.content,
        d.table_data,
        d.page_no,
        1 - (d.embedding <=> query_embedding) AS similarity
    FROM public.dfm_reference_docs d
    WHERE d.embedding IS NOT NULL
        AND (filter_source IS NULL OR d.source = filter_source)
        AND 1 - (d.embedding <=> query_embedding) >= min_similarity
    ORDER BY d.embedding <=> query_embedding
    LIMIT match_count;
$$;