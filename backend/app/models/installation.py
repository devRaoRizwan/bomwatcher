from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.tracked_repository import TrackedRepository
    from app.models.user import User


class GitHubInstallation(TimestampMixin, Base):
    __tablename__ = "github_installations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    account_login: Mapped[str] = mapped_column(String(100))
    account_type: Mapped[str] = mapped_column(String(20))
    repository_selection: Mapped[str] = mapped_column(String(20), default="all")

    user: Mapped["User"] = relationship(back_populates="installation")
    repositories: Mapped[list["TrackedRepository"]] = relationship(back_populates="installation", cascade="all, delete-orphan")
