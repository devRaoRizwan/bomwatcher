from collections.abc import Iterable

from sqlalchemy import func, select

from app.models import TrackedRepository
from app.repositories.base import BaseRepository


class TrackedRepositoryRepository(BaseRepository):
    def get(self, repository_id: int) -> TrackedRepository | None:
        return self.db.get(TrackedRepository, repository_id)

    def get_for_user(self, repository_id: int, user_id: int) -> TrackedRepository | None:
        repo = self.get(repository_id)
        return repo if repo and repo.user_id == user_id else None

    def list_for_user(self, user_id: int) -> list[TrackedRepository]:
        return list(self.db.scalars(select(TrackedRepository).where(TrackedRepository.user_id == user_id)))

    def count_for_user(self, user_id: int) -> int:
        return self.db.scalar(select(func.count()).where(TrackedRepository.user_id == user_id)) or 0

    def add(self, repo: TrackedRepository) -> TrackedRepository:
        self.db.add(repo)
        self.db.commit()
        return repo

    def delete(self, repo: TrackedRepository) -> None:
        self.db.delete(repo)
        self.db.commit()

    def delete_many(self, repository_ids: Iterable[int]) -> None:
        for repo in self.db.scalars(select(TrackedRepository).where(TrackedRepository.id.in_(list(repository_ids)))):
            self.db.delete(repo)
        self.db.commit()
