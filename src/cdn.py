from flask import Flask, request, send_file

from error import error_response

app = Flask(__name__)


@app.get("/upload")
def get_upload_page():
    return send_file("static/upload_page.html"), 200


@app.post("/upload")
def handle_file_upload():
    if request.mimetype != "multipart/form-data":
        return error_response("request mimetype invalid")
    if (file_count := len(request.files)) != 1:
        return error_response(f"received {file_count} files, expected 1")

    return "ok", 200


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
