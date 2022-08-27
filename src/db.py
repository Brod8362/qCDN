import sqlite3
from fileinfo import FileInformation

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
        cur.close()


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
    cur.close()
