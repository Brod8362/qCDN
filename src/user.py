import functools
from dataclasses import dataclass

from fileinfo import FileInformation
from util import format_file_size


@dataclass
class User:
    name: str
    size_limit: int
    quota: int
    admin: bool

    def quota_nice(self) -> str:
        return format_file_size(self.quota)

    def upload_info(self, db_conn) -> list[FileInformation]:
        # TODO: this function might be a performance bottleneck in the future, some caching is needed here
        return db_conn.get_user_uploads(self.name)

    def quota_used(self, db_conn) -> int:
        return sum(f.size for f in self.upload_info(db_conn))

    def quota_used_nice(self, db_conn) -> str:
        return format_file_size(self.quota_used(db_conn))

    def upload_count(self, db_conn) -> int:
        return len(self.upload_info(db_conn))
