from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, utcnow

if TYPE_CHECKING:
    from app.models.tracked_repository import TrackedRepository


class ScanStatus(StrEnum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"


class Scan(TimestampMixin, Base):
    __tablename__ = "scans"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    repository_id: Mapped[int] = mapped_column(ForeignKey("tracked_repositories.id", ondelete="CASCADE"), index=True)
    status: Mapped[ScanStatus] = mapped_column(String(20), default=ScanStatus.RUNNING)
    trigger: Mapped[str] = mapped_column(String(40))
    commit_sha: Mapped[str] = mapped_column(String(40))
    run_url: Mapped[str | None] = mapped_column(String(500))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    bom: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    error: Mapped[str | None] = mapped_column(Text)

    repository: Mapped["TrackedRepository"] = relationship(back_populates="scans")
