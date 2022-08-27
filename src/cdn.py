import hashlib
import functools
import os
import secrets
import uuid
from datetime import datetime

import magic
from flask import Flask, request, send_file, render_template

import db
from error import error_response
from fileinfo import FileInformation
from user import User
from util import format_file_size

# Constants
FILES_STORE_PATH = os.path.abspath("./files/")
DB_NAME = "qcdn.db"
MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1 GB

# Create flask app
app = Flask(__name__, template_folder="static")
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE

# Initialize database
db.init_db()


def get_database() -> db.CDNDatabase:
    return db.CDNDatabase(DB_NAME)


def auto_auth(force_auth=False):
    def decorator(f):
        @functools.wraps(f)
        def inner(*args, **kwargs):
            db_conn = get_database()
            user = db_conn.get_user_by_token(request.cookies.get("token", ""))
            if force_auth and user is None:
                return error_response("auth required", code=401)
            return f(user, *args, **kwargs)

        return inner

    return decorator


#
# ALL ENDPOINTS START HERE
#

# noinspection PyUnresolvedReferences
@app.get("/upload")
@auto_auth(force_auth=True)
def get_upload_page(user: User):
    db_conn = get_database()
    remaining = -1 if user.quota == -1 else user.quota - user.quota_used(db_conn)
    user_max = MAX_FILE_SIZE if user.size_limit == -1 else min(MAX_FILE_SIZE, user.size_limit)
    return render_template("upload_page.html", max_file_size=user_max, remaining_quota=remaining), 200


@app.post("/upload")
@auto_auth(force_auth=True)
def handle_file_upload(user: User):
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

    db_conn = get_database()

    try:
        uploaded_file = request.files["file"]
    except KeyError:
        return error_response(f"file not provided via 'file' parameter")
    file_id = str(uuid.uuid4())
    file_content = uploaded_file.stream.read()

    if user.quota != -1 and user.quota_used(db_conn) + len(file_content) > user.quota:
        return error_response("quota exceeded", 403)

    if user.size_limit != -1 and len(file_content) > user.size_limit:
        return error_response("file exceeds user size limit", 413)

    # construct FileInformation object
    file_info = FileInformation(
        id=file_id,
        mimetype=magic.from_buffer(file_content, mime=True),
        name=os.path.basename(uploaded_file.filename),
        size=len(file_content),
        checksum=hashlib.sha256(file_content).hexdigest(),
        upload_time=datetime.now(),
        expire_time=expires,
        modify_token="",
        uploader=user.name,
        owner_id=user.id
    )

    # insert metadata into database
    db_conn.save_file_info(file_info)

    # save file to disk
    os.makedirs(FILES_STORE_PATH, exist_ok=True)
    with open(os.path.join(FILES_STORE_PATH, file_info.id), "wb") as fd:
        fd.write(file_content)

    # return it
    resp = {
        "file_info": file_info.to_dict(base_url=request.url_root),
    }
    return resp, 201


@app.get("/file/<id>")
def get_file_info(id: str):
    db_conn = get_database()

    file_info = db_conn.get_file_info(id)
    if file_info is not None:
        return file_info.to_dict(base_url=request.url_root), 200
    else:
        return error_response("file not found"), 404


@app.delete("/file/<id>")
@auto_auth(force_auth=True)
def delete_file(user, id: str):
    db_conn = get_database()
    file_info = db_conn.get_file_info(id)
    if file_info is None:
        return error_response("file not found"), 404

    if user.admin or file_info.owner_id == user.id:
        file_path = os.path.join(FILES_STORE_PATH, file_info.id)
        db_conn.mark_deleted(file_info.id)
        os.remove(file_path)

        return "", 200
    else:
        return error_response("permission denied"), 403


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
@auto_auth(force_auth=True)
def retrieve_stats(user):
    if not user.admin:
        return error_response("unauthorized"), 403
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


# noinspection PyUnresolvedReferences
@app.get("/user")
@auto_auth()
def user_page(user):
    db_conn = get_database()
    info = {}
    files = []
    if user:
        files = user.upload_info(db_conn)
        info["quota_used"] = user.quota_used_nice(db_conn)
        info["quota"] = user.quota_nice() if user.quota != -1 else "unlimited"
        info["upload_count"] = user.upload_count(db_conn)
        info["size_limit"] = format_file_size(user.size_limit) if user.size_limit != -1 else "n/a"
    return render_template("register_page.html", user=user, info=info, files=files)


@app.post("/wizard")
@auto_auth()
def create_user(user):
    if (user is not None and user.admin) or request.remote_addr == "127.0.0.1":

        req = ["user", "quota", "file_size_limit"]
        for x in req:
            if x not in request.form:
                return error_response(f"missing {x} in form data", 400)
        id = uuid.uuid4()
        name = request.form["user"]
        try:
            quota_bytes = int(request.form["quota"])
            file_size_limit_bytes = int(request.form["file_size_limit"])
        except ValueError:
            return error_response("cannot parse int", 400)
        token = secrets.token_hex(nbytes=128)
        db_conn = get_database()
        db_conn.create_user(name, str(id), token, quota_bytes, file_size_limit_bytes)
        return {
                   "user": {
                       "id": id,
                       "name": name,
                       "quota": quota_bytes,
                       "file_size_limit_bytes": file_size_limit_bytes
                   },
                   "token": token,
               }, 201
    else:
        return error_response("unauthorized", 401)

# noinspection PyUnresolvedReferences
@app.get("/wizard")
@auto_auth()
def user_creation_wizard(user):
    if (user is not None and user.admin) or request.remote_addr == "127.0.0.1":
        return render_template("user_wizard.html")
    return error_response("unauthorized", 401)


#
# END OF ENDPOINTS
#
