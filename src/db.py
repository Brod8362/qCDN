import datetime
import sqlite3
from typing import Optional

from fileinfo import FileInformation
from datetime import datetime

DEFAULT_PATH = "qcdn.db"

class CDNDatabase:
    conn: sqlite3.Connection = None

    def __init__(self, path: str = DEFAULT_PATH):
        self.conn = sqlite3.connect(path)

    def __del__(self):
        self.conn.close()

    def save_file_info(self, info: FileInformation):
        cur = self.conn.cursor()
        cur.execute("INSERT INTO file_info VALUES(?,?,?,?,?,?,?,?,?)",
                    (info.id,
                     info.mimetype,
                     info.name,
                     info.size,
                     info.checksum,
                     info.upload_time,
                     info.expire_time,
                     info.modify_token,
                     info.uploader)
                    )
        self.conn.commit()
        cur.close()

    def get_file_info(self, file_id: str) -> Optional[FileInformation]:
        cur = self.conn.cursor()
        rs = [row for row in cur.execute(
            """SELECT mimetype, name, size, checksum, 
                upload_time, expire_time, modify_token, uploader
                FROM file_info WHERE id=?""",
            (file_id,)
        )]
        if len(rs) == 0:
            return None
        else:
            row = rs[0]
            return FileInformation(
                id=file_id,
                mimetype=row[0],
                name=row[1],
                size=row[2],
                checksum=row[3],
                upload_time=datetime.fromisoformat(row[4]),
                expire_time=datetime.fromisoformat(et) if (et := row[5]) is not None else None,
                modify_token=row[6],
                uploader=row[7]
            )


def init_db(path: str = DEFAULT_PATH):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS metadata(key TEXT NOT NULL PRIMARY KEY, value TEXT)")
    cur.execute("""CREATE TABLE IF NOT EXISTS file_info(
                    id TEXT NOT NULL PRIMARY KEY,
                    mimetype TEXT,
                    name TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    checksum TEXT NOT NULL,
                    upload_time TIMESTAMP NOT NULL,
                    expire_time TIMESTAMP,
                    modify_token TEXT,
                    uploader TEXT
                )""")
    conn.commit()
    cur.close()
