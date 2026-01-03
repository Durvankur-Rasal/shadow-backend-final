from fastapi import FastAPI, BackgroundTasks, HTTPException, Header
from pydantic import BaseModel
from src.runner import run_review_task
import os

app = FastAPI(title="Shadow Reviewer API")

class WebhookPayload(BaseModel):
    repo_name: str
    pr_number: int
    secret_token: str  # Simple security check

@app.get("/")
def health_check():
    return {"status": "active", "service": "Shadow Reviewer"}

@app.post("/review")
async def trigger_review(payload: WebhookPayload, background_tasks: BackgroundTasks):
    """
    Receives the webhook and runs the review in the background.
    Returns 202 Accepted immediately so GitHub doesn't timeout.
    """
    # 1. Verify Secret (Basic Security)
    if payload.secret_token != os.getenv("API_SECRET", "default-secret"):
        raise HTTPException(status_code=401, detail="Invalid Secret Token")

    # 2. Add to Background Queue (Fire and Forget)
    background_tasks.add_task(run_review_task, payload.repo_name, payload.pr_number)

    return {"message": "Review queued", "repo": payload.repo_name, "pr": payload.pr_number}

# For local testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)