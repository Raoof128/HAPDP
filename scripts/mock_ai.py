"""Simple FastAPI mock that emulates an AI analysis endpoint."""
from __future__ import annotations

from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Mock AI Endpoint")


class AnalysisRequest(BaseModel):
    resourceType: str


@app.post("/analyse")
async def analyse(payload: AnalysisRequest):  # pragma: no cover - utility script
    if payload.resourceType not in {"Patient", "Observation", "Encounter", "Condition"}:
        raise HTTPException(status_code=400, detail="Unsupported resource type")
    return {
        "resourceType": payload.resourceType,
        "analysis": "accepted",
        "received_at": datetime.utcnow().isoformat() + "Z",
    }


def main() -> None:
    import uvicorn

    uvicorn.run("scripts.mock_ai:app", host="0.0.0.0", port=9000, reload=False)


if __name__ == "__main__":
    main()
