from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import util

@dataclass
class FileInformation:
    id: str
    mimetype: str
    name: str
    size: int
    checksum: str
    upload_time: datetime
    expire_time: Optional[datetime]
    modify_token: str
    uploader: Optional[str]
    owner_id: Optional[str]

    def is_expired(self):
        return self.expire_time is not None and self.expire_time < datetime.now()

    def download_url(self, base: str = ""):
        return f"{base}/file/{self.id}/download"

    def size_nice(self) -> str:
        return util.format_file_size(self.size)

    def to_dict(self, base_url: str = ""):
        return {
            "id": self.id,
            "mimetype": self.mimetype,
            "size": self.size,
            "name": self.name,
            "checksum": self.checksum,
            "upload_time": self.upload_time.isoformat(),
            "expire_time": self.expire_time.isoformat() if self.expire_time is not None else None,
            "download_url": self.download_url(base=base_url)
        }
