#!/usr/bin/env python3
"""
Debug: show subjects and snippets of Piraeus Bank emails to understand format.
"""
import os, re, base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE  = os.path.join(SCRIPT_DIR, "token_damoncollective.json")
CREDS_FILE  = os.path.join(SCRIPT_DIR, "credentials_damoncollective.json")
SCOPES      = ["https://www.googleapis.com/auth/gmail.modify"]

def get_service():
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build("gmail", "v1", credentials=creds)

def get_body(payload):
    body = ""
    if "parts" in payload:
        for part in payload["parts"]:
            body += get_body(part)
    else:
        data = payload.get("body", {}).get("data", "")
        if data:
            decoded = base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
            body += decoded
    return body

service = get_service()

QUERY = 'from:(piraeusbank OR winbank OR pireausbank OR "piraeus" OR "winbank.gr" OR "piraeusbank.gr") after:2024/12/31'
resp  = service.users().messages().list(userId="me", q=QUERY, maxResults=10).execute()
msgs  = resp.get("messages", [])

print(f"Showing first {len(msgs)} Piraeus emails:\n")

for msg_ref in msgs:
    msg = service.users().messages().get(userId="me", id=msg_ref["id"], format="full").execute()
    headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
    subject = headers.get("Subject", "")
    sender  = headers.get("From", "")
    date    = headers.get("Date", "")[:25]
    body    = get_body(msg["payload"])
    clean   = re.sub(r"<[^>]+>", " ", body)
    clean   = re.sub(r"\s+", " ", clean).strip()

    print(f"FROM   : {sender}")
    print(f"DATE   : {date}")
    print(f"SUBJECT: {subject}")
    print(f"BODY   : {clean[:600]}")
    print("-" * 80)
