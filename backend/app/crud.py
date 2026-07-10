from app.database import supabase
from app.schemas import AnalysisResult, AnalysisDBRecord

TABLE_NAME = "analysis_jobs"


def insert_analysis_result(result: AnalysisResult) -> dict:
    """
    Validates and inserts a completed analysis result into Supabase.
    The full result payload is stored as JSON in the results_json column.
    Returns the inserted row from Supabase.
    """
    record = AnalysisDBRecord(
        analysis_id=result.analysis_id,
        filename=result.filename,
        status=result.status.value,
        manufacturability_score=result.manufacturability_score,
        results_json=result.model_dump(),
    )

    response = (
        supabase
        .table(TABLE_NAME)
        .insert(record.model_dump())
        .execute()
    )

    return response.data


def get_analysis_by_id(analysis_id: str) -> dict | None:
    """
    Fetches a single analysis record from Supabase by analysis_id.
    Returns None if not found.
    """
    response = (
        supabase
        .table(TABLE_NAME)
        .select("*")
        .eq("analysis_id", analysis_id)
        .single()
        .execute()
    )

    return response.data if response.data else None