#!/usr/bin/env python3
"""Minimal client: send one message, print only the answer.

    ./client.py "hi, what do you do?"
    ./client.py --session <id> "and now?"     # continue a session
    BASE=http://host:8765 ./client.py "hi"
"""
import argparse
import json
import os
import urllib.request

BASE = os.environ.get("BASE", "http://127.0.0.1:8765")


def post(message: str, session_id: str | None = None) -> dict:
    body = {"message": message}
    if session_id:
        body["session_id"] = session_id
    req = urllib.request.Request(
        f"{BASE}/chat",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("message")
    ap.add_argument("--session", dest="session_id")
    args = ap.parse_args()

    print(post(args.message, args.session_id)["answer"])
