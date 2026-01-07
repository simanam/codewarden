"""CodeWarden Projects Router - Project management endpoints."""

from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/projects", tags=["Projects"])


class ProjectCreate(BaseModel):
    """Request to create a new project."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    environment: str = "production"


class Project(BaseModel):
    """A CodeWarden project."""

    id: str
    name: str
    description: str | None = None
    environment: str
    api_key: str
    dsn: str
    created_at: str
    updated_at: str


class ProjectList(BaseModel):
    """List of projects."""

    projects: list[Project]
    total: int


def verify_user_token(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    """Verify user authentication token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization token",
        )

    token = authorization[7:]  # Remove "Bearer " prefix

    # TODO: Validate JWT token and extract user ID
    # For now, return a placeholder user ID
    return "user_placeholder"


def generate_api_key() -> str:
    """Generate a secure API key."""
    return f"cw_{secrets.token_urlsafe(32)}"


def generate_dsn(project_id: str, api_key: str) -> str:
    """Generate a DSN for SDK configuration."""
    # Format: https://<api_key>@ingest.codewarden.io/<project_id>
    return f"https://{api_key}@ingest.codewarden.io/{project_id}"


@router.post(
    "/",
    response_model=Project,
    status_code=status.HTTP_201_CREATED,
    summary="Create project",
    description="Create a new project and generate API credentials.",
)
async def create_project(
    request: ProjectCreate,
    user_id: Annotated[str, Depends(verify_user_token)],
) -> Project:
    """Create a new project."""
    project_id = str(uuid.uuid4())
    api_key = generate_api_key()
    now = datetime.now(UTC).isoformat()

    # TODO: Store project in database
    project = Project(
        id=project_id,
        name=request.name,
        description=request.description,
        environment=request.environment,
        api_key=api_key,
        dsn=generate_dsn(project_id, api_key),
        created_at=now,
        updated_at=now,
    )

    return project


@router.get(
    "/",
    response_model=ProjectList,
    summary="List projects",
    description="List all projects for the authenticated user.",
)
async def list_projects(
    user_id: Annotated[str, Depends(verify_user_token)],
) -> ProjectList:
    """List all projects for the current user."""
    # TODO: Fetch projects from database
    return ProjectList(projects=[], total=0)


@router.get(
    "/{project_id}",
    response_model=Project,
    summary="Get project",
    description="Get a specific project by ID.",
)
async def get_project(
    project_id: str,
    user_id: Annotated[str, Depends(verify_user_token)],
) -> Project:
    """Get a specific project."""
    # TODO: Fetch project from database
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Project {project_id} not found",
    )


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete project",
    description="Delete a project and all associated data.",
)
async def delete_project(
    project_id: str,
    user_id: Annotated[str, Depends(verify_user_token)],
) -> Response:
    """Delete a project."""
    # TODO: Delete project from database
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Project {project_id} not found",
    )


@router.post(
    "/{project_id}/rotate-key",
    response_model=Project,
    summary="Rotate API key",
    description="Generate a new API key for the project.",
)
async def rotate_api_key(
    project_id: str,
    user_id: Annotated[str, Depends(verify_user_token)],
) -> Project:
    """Rotate the API key for a project."""
    # TODO: Update project with new API key
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Project {project_id} not found",
    )
