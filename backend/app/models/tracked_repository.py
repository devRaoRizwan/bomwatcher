from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.installation import GitHubInstallation
    from app.models.scan import Scan


class TrackedRepository(TimestampMixin, Base):
    __tablename__ = "tracked_repositories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    installation_id: Mapped[int] = mapped_column(ForeignKey("github_installations.id", ondelete="CASCADE"), index=True)

    full_name: Mapped[str] = mapped_column(String(200))
    default_branch: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(1000))
    language: Mapped[str | None] = mapped_column(String(50))
    is_private: Mapped[bool] = mapped_column(default=True)
    stars: Mapped[int] = mapped_column(Integer, default=0)

    pr_number: Mapped[int | None] = mapped_column(Integer)
    pr_url: Mapped[str | None] = mapped_column(String(500))
    pr_merged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scan_dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    installation: Mapped["GitHubInstallation"] = relationship(back_populates="repositories")
    scans: Mapped[list["Scan"]] = relationship(
        back_populates="repository",
        cascade="all, delete-orphan",
        order_by="(Scan.started_at.desc(), Scan.id.desc())",
    )
