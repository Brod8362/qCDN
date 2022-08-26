from flask import Flask, request

app = Flask(__name__)


@app.get("/upload")
def get_upload_page():
    return "not implemented", 501


@app.post("/upload")
def handle_file_upload():
    return "not implemented", 501


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
