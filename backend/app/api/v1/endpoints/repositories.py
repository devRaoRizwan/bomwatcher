from typing import Annotated, Any

from fastapi import APIRouter, Depends, status

from app.api.deps import CurrentUser, get_repository_service
from app.schemas.repository import (
    EnableRepositoriesRequest,
    EnableRepositoriesResponse,
    RepositoryDetail,
    RepositoryRead,
    UsageRead,
)
from app.services.repository_service import RepositoryService

router = APIRouter(tags=["repositories"])
Repos = Annotated[RepositoryService, Depends(get_repository_service)]


@router.get("/usage", response_model=UsageRead)
def usage(user: CurrentUser, service: Repos):
    return service.usage(user)


@router.get("/repos", response_model=list[RepositoryRead])
def list_repositories(user: CurrentUser, service: Repos):
    return service.list_repositories(user)


@router.post("/repos/enable", response_model=EnableRepositoriesResponse)
def enable_repositories(data: EnableRepositoriesRequest, user: CurrentUser, service: Repos):
    return service.enable(user, data.repo_ids)


@router.delete("/repos/{repository_id}/enable", status_code=status.HTTP_204_NO_CONTENT)
def disable_repository(repository_id: int, user: CurrentUser, service: Repos):
    service.disable(user, repository_id)


@router.get("/repos/{repository_id}", response_model=RepositoryDetail)
def get_repository(repository_id: int, user: CurrentUser, service: Repos):
    return service.get_repository(user, repository_id)


@router.get("/repos/{repository_id}/bom", response_model=dict[str, Any])
def latest_bom(repository_id: int, user: CurrentUser, service: Repos):
    return service.latest_bom(user, repository_id)


@router.get("/repos/{repository_id}/scans/{scan_id}/bom", response_model=dict[str, Any])
def scan_bom(repository_id: int, scan_id: int, user: CurrentUser, service: Repos):
    return service.scan_bom(user, repository_id, scan_id)


@router.post("/repos/{repository_id}/scans", status_code=status.HTTP_202_ACCEPTED)
def request_scan(repository_id: int, user: CurrentUser, service: Repos) -> dict[str, bool]:
    service.rescan(user, repository_id)
    return {"dispatched": True}
