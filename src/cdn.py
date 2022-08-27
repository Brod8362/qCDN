import hashlib
import os
import uuid
from datetime import datetime

import magic
from flask import Flask, request, send_file, render_template

import db
from error import error_response
from fileinfo import FileInformation
from util import format_file_size

# Constants
FILES_STORE_PATH = os.path.abspath("./files/")
DB_NAME = "qcdn.db"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

# Create flask app
app = Flask(__name__, template_folder="static")
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE

# Initialize database
db.init_db()


def get_database() -> db.CDNDatabase:
    return db.CDNDatabase(DB_NAME)


# noinspection PyUnresolvedReferences
@app.get("/upload")
def get_upload_page():
    return render_template("upload_page.html", max_file_size=MAX_FILE_SIZE), 200


@app.post("/upload")
def handle_file_upload():
    if request.mimetype != "multipart/form-data":
        return error_response("request mimetype invalid")
    if (file_count := len(request.files)) != 1:
        return error_response(f"received {file_count} files, expected 1")

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
        uploader=request.remote_addr
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
        "file_info": file_info.to_dict(base_url=request.host_url),
        "modify_token": file_info.modify_token,
    }
    return resp, 201


@app.get("/file/<id>")
def get_file_info(id: str):
    db_conn = get_database()

    file_info = db_conn.get_file_info(id)
    if file_info is not None:
        return file_info.to_dict(), 200
    else:
        return error_response("file not found"), 404


@app.delete("/file/<id>")
def delete_file(id: str):
    # TODO: maybe make this a parameter?
    if request.content_type != "text/plain":
        return error_response("wrong content type (expected text/plain)", 400)

    db_conn = get_database()
    file_info = db_conn.get_file_info(id)
    if file_info is None:
        return error_response("file not found"), 404

    token = request.stream.read()
    if token != file_info.modify_token:
        return error_response("incorrect token"), 403
    else:
        # TODO: delete the file
        return "", 200


@app.get("/file/<id>/download")
def download_file(id: str):
    db_conn = get_database()
    file_info = db_conn.get_file_info(id)
    if file_info is None:
        return error_response("file not found"), 404

    if file_info.is_expired():
        return error_response("download expired"), 410

    return send_file(os.path.join(FILES_STORE_PATH, file_info.id), download_name=file_info.name)


# noinspection PyUnresolvedReferences
@app.get("/stats")
def retrieve_stats():
    db_conn = get_database()
    files = db_conn.get_all_file_info()
    stats = {
        "total_files": len(files),
        "total_size": format_file_size(sum(f.size for f in files)),
        "largest_file": format_file_size(max(f.size for f in files)),
        "maximum_allowed": format_file_size(MAX_FILE_SIZE)
    }
    files.sort(key=lambda x: x.size, reverse=True)
    return render_template("stats_page.html", stats=stats, files=files), 200
