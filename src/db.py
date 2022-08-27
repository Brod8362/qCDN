import sqlite3
from fileinfo import FileInformation


class CDNDatabase:
    conn: sqlite3.Connection = None

    def __init__(self, path: str = "qcdn.db"):
        self.conn = sqlite3.connect(path)

    def __del__(self):
        self.conn.close()

    def create_tables(self):
        cur = self.conn.cursor()
        cur.execute("CREATE TABLE metadata(key TEXT NOT NULL, value TEXT) IF NOT EXISTS")
        cur.execute("""CREATE TABLE file_info(
                        id: TEXT NOT NULL PRIMARY KEY,
                        mimetype: TEXT,
                        name: TEXT NOT NULL,
                        size: INTEGER NOT NULL,
                        checksum: TEXT NOT NULL,
                        upload_time: TIMESTAMP NOT NULL,
                        expire_time: TIMESTAMP,
                        modify_token: TEXT,
                        uploader: TEXT
                    ) IF NOT EXISTS""")
        cur.close()

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