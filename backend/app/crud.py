from app.database import LOCAL_MODE, supabase
from app import local_store
from app.schemas import AnalysisResult, AnalysisDBRecord

TABLE_NAME = "analysis_jobs"


def insert_analysis_result(result: AnalysisResult) -> list[dict]:
    """
    Validates and inserts an analysis into the configured record store.
    The full result payload is stored as JSON in the results_json column.
    Returns the inserted row data.
    """
    record = AnalysisDBRecord(
        analysis_id=result.analysis_id,
        filename=result.filename,
        status=result.status.value,
        manufacturability_score=result.manufacturability_score,
        results_json=result.model_dump(),
    )

    if LOCAL_MODE:
        return local_store.insert_record(record.model_dump(mode="json"))

    response = supabase.table(TABLE_NAME).insert(record.model_dump()).execute()

    return response.data


def get_analysis_by_id(analysis_id: str) -> dict | None:
    """
    Fetches a single analysis record by analysis_id.

    Args:
        analysis_id: The UUID of the analysis record to fetch.

    Returns:
        The analysis record as a dict if found, or None if no matching
        record exists.

    Raises:
        postgrest.exceptions.APIError: If the database request itself fails
        (e.g. invalid credentials, RLS rejection, connectivity issues).
    """
    if LOCAL_MODE:
        return local_store.get_record(analysis_id)

    # maybe_single() returns None for the whole response when no row matches.
    response = (
        supabase.table(TABLE_NAME)
        .select("*")
        .eq("analysis_id", analysis_id)
        .maybe_single()
        .execute()
    )

    return response.data if response else None


def update_analysis_status(
    analysis_id: str,
    status: str,
    extra_fields: dict | None = None,
) -> list[dict]:
    """
    Updates the status of an existing analysis record.
    Optionally updates additional fields (e.g. manufacturability_score, results_json)
    at the same time as the status change.

    Args:
        analysis_id: The UUID of the analysis record to update.
        status: The new status string (e.g. "processing", "completed", "failed").
        extra_fields: Optional dict of additional columns to update in the same call.

    Returns:
        The updated row data from the configured record store.
    """
    payload = {"status": status}
    if extra_fields:
        payload.update(extra_fields)

    if LOCAL_MODE:
        return local_store.update_record(analysis_id, payload)

    response = (
        supabase.table(TABLE_NAME)
        .update(payload)
        .eq("analysis_id", analysis_id)
        .execute()
    )

    return response.data
