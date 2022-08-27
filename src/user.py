from dataclasses import dataclass
from util import format_file_size


@dataclass
class User:
    name: str
    size_limit: int
    quota: int

    def quota_nice(self) -> str:
        return format_file_size(self.quota)

    def quota_used(self) -> int:
        # TODO: finish this
        return 0

    def quota_used_nice(self) -> str:
        return format_file_size(self.quota_used())

    def upload_count(self) -> int:
        return -1
