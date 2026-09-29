from functools import lru_cache

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.investigation_service import (
    get_investigation_service,
)


app = FastAPI(
    title="TraceAI API",
    description=(
        "Evidence-grounded GenAI API for software "
        "incident investigation and root cause analysis."
    ),
    version="1.0.0",
)


# -------------------------------------------------------------------
# Request models
# -------------------------------------------------------------------

class InvestigationRequest(BaseModel):
    incident_id: str = Field(
        ...,
        min_length=1,
        description="Incident to investigate.",
    )

    query: str = Field(
        ...,
        min_length=1,
        description="Investigation question.",
    )

    top_k: int = Field(
        default=8,
        ge=1,
        le=50,
        description="Number of evidence items to retrieve.",
    )


# -------------------------------------------------------------------
# Response models
# -------------------------------------------------------------------

class RootCauseResponse(BaseModel):
    name: str
    explanation: str
    confidence: str
    support_score: float


class VerificationResponse(BaseModel):
    citation_coverage: float
    groundedness: float
    claim_coverage: float | None = None
    citation_status: str
    groundedness_level: str
    claim_status: str


class EvidenceResponse(BaseModel):
    text: str
    source_type: str
    provenance: str
    source_file: str
    location: str
    metadata: dict


class InvestigationResponse(BaseModel):
    investigation_id: str
    incident_id: str
    query: str
    root_cause: RootCauseResponse
    analysis: str
    evidence: list[EvidenceResponse]
    verification: VerificationResponse


class InvestigationHistoryResponse(BaseModel):
    investigation_id: str
    incident_id: str
    query: str
    root_cause: str
    confidence: str
    confidence_score: float
    groundedness_score: float
    citation_coverage: float
    claim_coverage: float | None = None
    created_at: str


class InvestigationHistoryListResponse(BaseModel):
    count: int
    investigations: list[InvestigationHistoryResponse]


# -------------------------------------------------------------------
# Shared application service
# -------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_service():
    """
    Return the shared InvestigationService.

    The service is cached because the underlying
    IncidentInvestigator builds the embedding index
    during initialization.
    """

    return get_investigation_service()


# -------------------------------------------------------------------
# Response conversion
# -------------------------------------------------------------------

def build_api_response(result):
    """
    Convert the internal IncidentInvestigator result into
    the public API response schema.
    """

    root_cause = result.get(
        "root_cause_details",
        result.get("root_cause", {}),
    )

    if not root_cause:
        root_cause = {
            "root_cause": "Unknown",
            "explanation": (
                "No root cause could be determined "
                "from the available evidence."
            ),
            "confidence": "LOW",
            "support_score": 0.0,
        }

    verification = {
        "citation_coverage": result.get(
            "citation_verification",
            {},
        ).get(
            "citation_coverage",
            0.0,
        ),
        "groundedness": result.get(
            "groundedness",
            {},
        ).get(
            "score",
            0.0,
        ),
        "claim_coverage": result.get(
            "claim_verification",
            {},
        ).get(
            "claim_coverage",
        ),
        "citation_status": result.get(
            "citation_verification",
            {},
        ).get(
            "status",
            "FAIL",
        ),
        "groundedness_level": result.get(
            "groundedness",
            {},
        ).get(
            "level",
            "LOW",
        ),
        "claim_status": result.get(
            "claim_verification",
            {},
        ).get(
            "status",
            "FAIL",
        ),
    }

    evidence_items = []

    for item in result.get("evidence", []):
        evidence_items.append(
            {
                "text": item.get("text", ""),
                "source_type": item.get(
                    "source_type",
                    "",
                ),
                "provenance": item.get(
                    "provenance",
                    "",
                ),
                "source_file": item.get(
                    "source_file",
                    "",
                ),
                "location": item.get(
                    "location",
                    "",
                ),
                "metadata": item.get(
                    "metadata",
                    {},
                ),
            }
        )

    return {
        "investigation_id": result.get(
            "investigation_id",
            "",
        ),
        "incident_id": result.get(
            "incident_id",
            "",
        ),
        "query": result.get(
            "query",
            "",
        ),
        "root_cause": {
            "name": root_cause.get(
                "root_cause",
                "Unknown",
            ),
            "explanation": root_cause.get(
                "explanation",
                "",
            ),
            "confidence": root_cause.get(
                "confidence",
                result.get(
                    "root_cause_confidence",
                    "LOW",
                ),
            ),
            "support_score": root_cause.get(
                "support_score",
                0.0,
            ),
        },
        "analysis": result.get(
            "analysis",
            "",
        ),
        "evidence": evidence_items,
        "verification": verification,
    }


# -------------------------------------------------------------------
# Health
# -------------------------------------------------------------------




@app.get(
    "/api/v1/health",
)
def api_v1_health():
    return {
        "status": "ok",
        "service": "traceai-api",
        "version": "v1",
    }


# -------------------------------------------------------------------
# Incidents
# -------------------------------------------------------------------


@app.get(
    "/api/v1/incidents",
)
def api_v1_incidents():
    try:
        service = get_service()
        incident_ids = service.list_incidents()

        return {
            "count": len(incident_ids),
            "incidents": incident_ids,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# -------------------------------------------------------------------
# Investigations
# -------------------------------------------------------------------


@app.post(
    "/api/v1/investigations",
    response_model=InvestigationResponse,
)
def api_v1_investigations(
    request: InvestigationRequest,
):
    try:
        service = get_service()

        result = service.investigate(
            query=request.query,
            incident_id=request.incident_id,
            top_k=request.top_k,
        )

        return build_api_response(result)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# -------------------------------------------------------------------
# Investigation history
# -------------------------------------------------------------------

@app.get(
    "/api/v1/investigations",
    response_model=InvestigationHistoryListResponse,
)
def api_v1_investigation_history(
    limit: int = Query(
        default=25,
        ge=1,
        le=100,
    ),
):
    try:
        service = get_service()

        records = service.list_investigations(
            limit=limit,
        )

        return {
            "count": len(records),
            "investigations": records,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@app.get(
    "/api/v1/investigations/{investigation_id}",
    response_model=InvestigationHistoryResponse,
)
def api_v1_get_investigation(
    investigation_id: str,
):
    service = get_service()

    record = service.get_investigation(
        investigation_id,
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Investigation "
                f"'{investigation_id}' was not found."
            ),
        )

    return record


@app.delete(
    "/api/v1/investigations/{investigation_id}",
)
def api_v1_delete_investigation(
    investigation_id: str,
):
    service = get_service()

    deleted = service.delete_investigation(
        investigation_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Investigation "
                f"'{investigation_id}' was not found."
            ),
        )

    return {
        "status": "deleted",
        "investigation_id": investigation_id,
    }