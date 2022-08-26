import json

from flask import make_response


def error_response(msg: str, code: int = 400):
    r = make_response()
    r.status_code = code
    r.mimetype = "application/json"
    r.data = json.dumps({
        "error_str": msg
    })
    return r
