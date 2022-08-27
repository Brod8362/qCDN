import datetime
import sqlite3
from typing import Optional, List

from fileinfo import FileInformation
from user import User
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
            """SELECT id, mimetype, name, size, checksum, 
                upload_time, expire_time, modify_token, uploader
                FROM file_info WHERE id=?""",
            (file_id,)
        )]
        if len(rs) == 0:
            return None
        else:
            return row_to_obj(rs[0])

    def get_all_file_info(self) -> List[FileInformation]:
        cur = self.conn.cursor()
        rs_iter = cur.execute(
            """SELECT id, mimetype, name, size, checksum, 
                upload_time, expire_time, modify_token, uploader
                FROM file_info""")
        return [row_to_obj(row) for row in rs_iter]

    def get_user_by_token(self, token: str) -> Optional[User]:
        cur = self.conn.cursor()
        for row in cur.execute("SELECT name, file_size_limit, quota FROM users WHERE token=?", (token,)):
            return User(row[0], row[1], row[2])
        return None

    def get_user_uploads(self, user_name: str) -> List[FileInformation]:
        cur = self.conn.cursor()
        rs_iter = cur.execute(
            """SELECT id, mimetype, name, size, checksum, 
                upload_time, expire_time, modify_token, uploader
                FROM file_info WHERE uploader=?""", (user_name,))
        return [row_to_obj(row) for row in rs_iter]


def row_to_obj(row: tuple) -> FileInformation:
    return FileInformation(
        id=row[0],
        mimetype=row[1],
        name=row[2],
        size=row[3],
        checksum=row[4],
        upload_time=datetime.fromisoformat(row[5]),
        expire_time=datetime.fromisoformat(et) if (et := row[6]) is not None else None,
        modify_token=row[7],
        uploader=row[8]
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
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        token TEXT NOT NULL PRIMARY KEY,
        name TEXT,
        file_size_limit INTEGER,
        quota INTEGER
    )
    """)
    conn.commit()
    cur.close()
