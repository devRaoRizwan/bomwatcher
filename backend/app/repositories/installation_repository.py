from app.models import GitHubInstallation
from app.repositories.base import BaseRepository


class InstallationRepository(BaseRepository):
    def get(self, installation_id: int) -> GitHubInstallation | None:
        return self.db.get(GitHubInstallation, installation_id)

    def save(self, installation: GitHubInstallation) -> GitHubInstallation:
        self.db.add(installation)
        self.db.commit()
        self.db.refresh(installation)
        return installation

    def delete(self, installation: GitHubInstallation) -> None:
        self.db.delete(installation)
        self.db.commit()
