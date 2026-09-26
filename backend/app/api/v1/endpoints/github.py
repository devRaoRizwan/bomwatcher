from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import CurrentUser, get_github_connection_service
from app.schemas.github import InstallationCallback, InstallationRead, InstallUrlResponse
from app.services import presenters
from app.services.github_connection_service import GitHubConnectionService

router = APIRouter(prefix="/github", tags=["github"])
Connection = Annotated[GitHubConnectionService, Depends(get_github_connection_service)]


@router.get("/installation", response_model=InstallationRead | None)
def get_installation(user: CurrentUser):
    return presenters.installation_read(user.installation) if user.installation else None


@router.get("/install-url", response_model=InstallUrlResponse)
def get_install_url(user: CurrentUser, connection: Connection):
    return InstallUrlResponse(url=connection.install_url(user))


@router.post("/installation", response_model=InstallationRead)
def complete_installation(data: InstallationCallback, user: CurrentUser, connection: Connection):
    installation = connection.complete_installation(user, data.installation_id, data.state)
    return presenters.installation_read(installation)


@router.delete("/installation", status_code=status.HTTP_204_NO_CONTENT)
def disconnect(user: CurrentUser, connection: Connection):
    connection.disconnect(user)
