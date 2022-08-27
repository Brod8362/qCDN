#!/usr/bin/env python3
import os
import sys
import requests
import toml


def load_info():
    with open(os.path.expanduser("~/.cdn_info.toml"), "r") as fd:
        data = toml.load(fd)
    return data


try:
    CDN_TOKEN = os.environ["CDN_TOKEN"]
    CDN_HOST = os.environ["CDN_HOST"]
except KeyError:
    t = load_info()
    CDN_TOKEN = t["token"]
    CDN_HOST = t["host"]


def main():
    if len(sys.argv) < 2:
        sys.stderr.write("usage: qcdn_upload.py [source_file] <uploaded_file_name>\n")
        sys.stderr.flush()
        sys.exit(0)

    if sys.argv[1] == "-":
        if len(sys.argv) < 3:
            sys.stderr.write("filename required when reading from stdin\n")
            sys.stderr.flush()
            sys.exit(1)
        file = sys.stdin.buffer
        name = sys.argv[2]
    else:
        file = open(sys.argv[1], "rb")
        try:
            name = sys.argv[2]
        except IndexError:
            name = os.path.basename(sys.argv[1])

    try:
        response = requests.post(
            f"{CDN_HOST}/upload",
            headers={
                "Authorization": CDN_TOKEN
            },
            files=(
                ("file", (name, file)),
            )
        )
    finally:
        file.close()

    if response.status_code == 201:
        print(response.json()["file_info"]["download_url"])
    else:
        sys.stderr.write(f"failed: {response.status_code}: {response.content}")
        sys.stderr.flush()
        sys.exit(1)


if __name__ == "__main__":
    main()
