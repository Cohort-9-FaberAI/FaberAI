-- Migration: 01_create_analysis_jobs
-- Creates the analysis_jobs table to store CAD part analysis results

CREATE TABLE IF NOT EXISTS public.analysis_jobs (
    analysis_id     TEXT PRIMARY KEY,
    filename        TEXT NOT NULL,
    status          TEXT NOT NULL,
    manufacturability_score FLOAT,
    results_json    JSONB
);

-- RLS policy: permissive for development
ALTER TABLE public.analysis_jobs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "rls_policy_all"
ON public.analysis_jobs
AS PERMISSIVE
FOR ALL
TO public
USING (true)
WITH CHECK (true);