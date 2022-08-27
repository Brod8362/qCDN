from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class FileInformation:
    id: str
    mimetype: str
    name: str
    size: int
    checksum: str
    upload_time: datetime
    expire_time: Optional[datetime]
    download_url: str
    modify_token: str
    uploader: Optional[str]

    def is_expired(self):
        return self.expire_time is not None and self.expire_time < datetime.now()
