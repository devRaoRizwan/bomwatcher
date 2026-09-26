import logging

from app.core import security
from app.core.exceptions import BadRequestError, ConflictError, PermissionDeniedError, ServiceUnavailableError, UpstreamError
from app.integrations.github.client import GitHubAPIError, GitHubApp
from app.models import GitHubInstallation, User
from app.repositories.installation_repository import InstallationRepository

log = logging.getLogger(__name__)


class GitHubConnectionService:
    def __init__(self, installations: InstallationRepository, github: GitHubApp):
        self.installations = installations
        self.github = github

    def _require_configured(self) -> None:
        if not self.github.configured:
            raise ServiceUnavailableError("GitHub App is not configured on this server")

    def install_url(self, user: User) -> str:
        self._require_configured()
        return self.github.install_url(security.create_install_state(user.id))

    def complete_installation(self, user: User, installation_id: int, state: str) -> GitHubInstallation:
        self._require_configured()
        try:
            state_user_id = security.decode_install_state(state)
        except security.InvalidTokenError as e:
            raise BadRequestError("Install link expired or invalid. Start the connection again.") from e
        if state_user_id != user.id:
            raise PermissionDeniedError("This install link belongs to a different account")

        try:
            remote = self.github.get_installation(installation_id)
        except GitHubAPIError as e:
            raise BadRequestError("Could not verify the installation with GitHub") from e

        existing = self.installations.get(installation_id)
        if existing and existing.user_id != user.id:
            raise ConflictError("This GitHub installation is already linked to another BOMWatcher account")
        if user.installation and user.installation.id != installation_id:
            self.installations.delete(user.installation)

        installation = existing or GitHubInstallation(id=installation_id, user_id=user.id)
        installation.account_login = remote["account"]["login"]
        installation.account_type = remote["account"]["type"]
        installation.repository_selection = remote.get("repository_selection", "all")
        return self.installations.save(installation)

    def disconnect(self, user: User) -> None:
        installation = user.installation
        if installation is None:
            return
        if self.github.configured:
            try:
                self.github.delete_installation(installation.id)
            except GitHubAPIError as e:
                if e.status_code != 404:
                    raise UpstreamError("GitHub refused to remove the installation") from e
        self.installations.delete(installation)
