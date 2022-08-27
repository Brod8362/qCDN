import hashlib
import os
import uuid
from datetime import datetime

import magic
from flask import Flask, request, send_file

import db
from error import error_response
from fileinfo import FileInformation

# Constants
FILES_STORE_PATH = "files/"
DB_NAME = "qcdn.db"

# Create flask app
app = Flask(__name__)

# Initialize database
db.init_db()


def get_database() -> db.CDNDatabase:
    return db.CDNDatabase(DB_NAME)


@app.get("/upload")
def get_upload_page():
    return send_file("static/upload_page.html"), 200


@app.post("/upload")
def handle_file_upload():
    if request.mimetype != "multipart/form-data":
        return error_response("request mimetype invalid")
    if (file_count := len(request.files)) != 1:
        return error_response(f"received {file_count} files, expected 1")

    # TODO: try and parse expiry time
    if "expire_time" in request.form:
        try:
            expires = datetime.fromisoformat(request.form["expire_time"])
        except ValueError:
            return error_response(f"invalid iso date string for expire_time")
    else:
        expires = None

    try:
        uploaded_file = request.files["file"]
    except KeyError:
        return error_response(f"file not provided via 'file' parameter")
    file_id = str(uuid.uuid4())
    modify_token = str(uuid.uuid4())[:8]
    file_content = uploaded_file.stream.read()

    # construct FileInformation object
    file_info = FileInformation(
        id=file_id,
        mimetype=magic.from_buffer(file_content, mime=True),
        name=os.path.basename(uploaded_file.filename),
        size=len(file_content),
        checksum=hashlib.sha256(file_content).hexdigest(),
        upload_time=datetime.now(),
        expire_time=expires,
        modify_token=modify_token,
        uploader=request.origin
    )

    # insert metadata into database
    db_conn = get_database()
    db_conn.save_file_info(file_info)

    # save file to disk
    os.makedirs(FILES_STORE_PATH, exist_ok=True)
    with open(os.path.join(FILES_STORE_PATH, file_info.id), "wb") as fd:
        fd.write(file_content)

    # return it
    resp = {
        "file_info": file_info.to_dict(),
        "modify_token": file_info.modify_token,
    }
    return resp, 200


@app.get("/file/<id>")
def get_file_info(id: int):
    return "not implemented", 501


@app.delete("/file/<id>")
def delete_file(id: int):
    return "not implemented", 501


@app.get("/file/<id>/download")
def download_file(id: int):
    return "not implemented", 501


@app.get("/stats")
def retrieve_stats():
    pass
