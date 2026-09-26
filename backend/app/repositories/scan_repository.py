from app.models import Scan
from app.repositories.base import BaseRepository


class ScanRepository(BaseRepository):
    def get(self, scan_id: int) -> Scan | None:
        return self.db.get(Scan, scan_id)

    def add(self, scan: Scan) -> Scan:
        self.db.add(scan)
        return scan
