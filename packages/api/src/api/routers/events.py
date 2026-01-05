"""CodeWarden Events Router - Event ingestion endpoints."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status

from api.models.events import Event, EventBatch, EventResponse
from api.services.event_processor import EventProcessor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/events", tags=["Events"])


def get_event_processor() -> EventProcessor:
    """Dependency to get event processor."""
    return EventProcessor()


def verify_api_key(
    x_api_key: Annotated[str | None, Header()] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    """
    Verify API key from headers.

    Accepts either X-API-Key header or Bearer token in Authorization header.
    """
    api_key = None

    if x_api_key:
        api_key = x_api_key
    elif authorization and authorization.startswith("Bearer "):
        api_key = authorization[7:]  # Remove "Bearer " prefix

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide X-API-Key header or Bearer token.",
        )

    # TODO: Validate API key against database
    # For now, accept any non-empty key
    return api_key


@router.post(
    "/ingest",
    response_model=EventResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest events",
    description="Receive and process a batch of events from SDK clients.",
)
async def ingest_events(
    batch: EventBatch,
    api_key: Annotated[str, Depends(verify_api_key)],
    processor: Annotated[EventProcessor, Depends(get_event_processor)],
) -> EventResponse:
    """
    Ingest a batch of events.

    Events are validated, enriched, and queued for processing.
    PII scrubbing is applied based on project settings.
    """
    try:
        event_ids = await processor.process_batch(batch.events, api_key)
        return EventResponse(
            success=True,
            event_ids=event_ids,
            message=f"Successfully received {len(event_ids)} events",
        )
    except Exception as e:
        logger.exception("Failed to process event batch")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process events: {str(e)}",
        )


@router.post(
    "/single",
    response_model=EventResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest single event",
    description="Receive and process a single event.",
)
async def ingest_single_event(
    event: Event,
    api_key: Annotated[str, Depends(verify_api_key)],
    processor: Annotated[EventProcessor, Depends(get_event_processor)],
) -> EventResponse:
    """Ingest a single event."""
    try:
        event_ids = await processor.process_batch([event], api_key)
        return EventResponse(
            success=True,
            event_ids=event_ids,
            message="Event received successfully",
        )
    except Exception as e:
        logger.exception("Failed to process event")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process event: {str(e)}",
        )


@router.get(
    "/{event_id}",
    response_model=Event,
    summary="Get event by ID",
    description="Retrieve a specific event by its ID.",
)
async def get_event(
    event_id: str,
    api_key: Annotated[str, Depends(verify_api_key)],
) -> Event:
    """Get a specific event by ID."""
    # TODO: Implement event retrieval from storage
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Event retrieval not yet implemented",
    )
