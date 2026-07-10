import os

from supabase import Client, create_client

# Table where the worker stores the final analysis for each Celery task.
ANALYSES_TABLE = "analyses"

_client: Client | None = None


def get_supabase_client() -> Client:
    """
    Returns a lazily-initialized Supabase client.
    Requires the SUPABASE_URL and SUPABASE_KEY environment variables.
    """
    global _client
    if _client is None:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        if not url or not key:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_KEY environment variables must be set."
            )
        _client = create_client(url, key)
    return _client


def fetch_analysis_by_task_id(task_id: str) -> dict | None:
    """
    Fetches the analysis row associated with a Celery task id.
    Returns None if no row exists for that task id.
    """
    client = get_supabase_client()
    response = (
        client.table(ANALYSES_TABLE)
        .select("*")
        .eq("task_id", task_id)
        .limit(1)
        .execute()
    )
    if response.data:
        return response.data[0]
    return None
