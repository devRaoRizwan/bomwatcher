import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from app.db.base import utcnow
from app.integrations.github.client import GitHubApp
from app.integrations.github.constants import PR_BRANCH, WORKFLOW_PATH
from app.models import Scan, ScanStatus
from app.repositories.installation_repository import InstallationRepository
from app.repositories.scan_repository import ScanRepository
from app.repositories.tracked_repository_repository import TrackedRepositoryRepository
from app.services.bom import is_cyclonedx

log = logging.getLogger(__name__)

BackgroundJob = Callable[[], None]


def _parse_time(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


class WebhookService:
    def __init__(self, db: Session, session_factory: sessionmaker, github: GitHubApp):
        self.db = db
        self.session_factory = session_factory
        self.github = github
        self.installations = InstallationRepository(db)
        self.repos = TrackedRepositoryRepository(db)
        self.scans = ScanRepository(db)

    def handle(self, event: str, payload: dict[str, Any]) -> BackgroundJob | None:
        handler = {
            "installation": self._installation,
            "installation_repositories": self._installation_repositories,
            "pull_request": self._pull_request,
            "workflow_run": self._workflow_run,
        }.get(event)
        return handler(payload) if handler else None

    def _installation(self, payload: dict[str, Any]) -> None:
        if payload.get("action") != "deleted":
            return None
        installation = self.installations.get(payload["installation"]["id"])
        if installation:
            self.installations.delete(installation)
        return None

    def _installation_repositories(self, payload: dict[str, Any]) -> None:
        removed = [r["id"] for r in payload.get("repositories_removed", [])]
        if removed:
            self.repos.delete_many(removed)
        return None

    def _pull_request(self, payload: dict[str, Any]) -> None:
        pr = payload["pull_request"]
        if payload.get("action") != "closed" or not pr.get("merged") or pr["head"]["ref"] != PR_BRANCH:
            return None
        repo = self.repos.get(payload["repository"]["id"])
        if repo and repo.pr_merged_at is None:
            repo.pr_merged_at = _parse_time(pr.get("merged_at")) or utcnow()
            self.repos.commit()
        return None

    def _workflow_run(self, payload: dict[str, Any]) -> BackgroundJob | None:
        run = payload["workflow_run"]
        if run.get("path") != WORKFLOW_PATH:
            return None
        repo = self.repos.get(payload["repository"]["id"])
        if repo is None:
            return None

        if repo.pr_merged_at is None:
            repo.pr_merged_at = utcnow()
        repo.scan_dispatched_at = None

        scan = self.scans.get(run["id"])
        if scan is None:
            scan = self.scans.add(Scan(
                id=run["id"],
                repository_id=repo.id,
                trigger=run.get("event", "unknown")[:40],
                commit_sha=run["head_sha"],
                run_url=run.get("html_url"),
                started_at=_parse_time(run.get("run_started_at")) or utcnow(),
            ))

        job = None
        if payload.get("action") == "completed":
            if run.get("conclusion") == "success":
                job = self._ingest_job(repo.installation_id, repo.full_name, run["id"], _parse_time(run.get("updated_at")))
            else:
                scan.status = ScanStatus.FAILURE
                scan.error = f"Workflow concluded: {run.get('conclusion')}"
                scan.finished_at = _parse_time(run.get("updated_at")) or utcnow()
        self.db.commit()
        return job

    def _ingest_job(self, installation_id: int, full_name: str, run_id: int, finished_at: datetime | None) -> BackgroundJob:
        def run() -> None:
            with self.session_factory() as db:
                scan = ScanRepository(db).get(run_id)
                if scan is None:
                    return
                try:
                    bom = self.github.for_installation(installation_id).download_bom(full_name, run_id)
                    if not is_cyclonedx(bom):
                        raise ValueError("artifact is not a CycloneDX BOM")
                    scan.bom = bom
                    scan.status = ScanStatus.SUCCESS
                except Exception as e:
                    log.exception("BOM ingest failed for %s run %s", full_name, run_id)
                    scan.status = ScanStatus.FAILURE
                    scan.error = f"Could not ingest BOM: {e}"
                scan.finished_at = finished_at or utcnow()
                db.commit()

        return run
