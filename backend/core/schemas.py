from pydantic import BaseModel, ConfigDict


class AnalysisResult(BaseModel):
    """
    Final analysis payload returned to the frontend, matching the API
    contract established by the /analyze-mock endpoint. Extra fields
    stored in the database are passed through untouched.
    """

    model_config = ConfigDict(extra="allow")

    analysis_id: str
    filename: str
    status: str
    manufacturability_score: int
    summary: str
    part_metadata: dict
    issues: list[dict]
