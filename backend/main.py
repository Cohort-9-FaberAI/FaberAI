from fastapi import FastAPI

app = FastAPI(
    title="FaberAI Backend",
    description="AI-powered manufacturability review API for CAD parts.",
    version="0.1.0",
)


@app.get("/", tags=["Health"])
def health_check():
    """
    Health check endpoint.
    Returns 200 OK to confirm the server is running.
    """
    return {"status": "ok", "message": "FaberAI backend is running."}