#!/usr/bin/env python3
"""Show full cleaned body of one Piraeus transaction email."""
import os, re, base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE  = os.path.join(SCRIPT_DIR, "token_damoncollective.json")
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

QUERY = 'from:IBankV2Email@piraeusbank.gr subject:"Ενημέρωση Εγχρήματης Συναλλαγής" after:2024/12/31'
resp  = service.users().messages().list(userId="me", q=QUERY, maxResults=3).execute()
msgs  = resp.get("messages", [])

for msg_ref in msgs[:2]:
    msg  = service.users().messages().get(userId="me", id=msg_ref["id"], format="full").execute()
    headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
    print("DATE   :", headers.get("Date","")[:25])
    print("SUBJECT:", headers.get("Subject",""))
    body = get_body(msg["payload"])
    # Strip CSS block (everything between style tags)
    clean = re.sub(r'<style[^>]*>.*?</style>', '', body, flags=re.DOTALL|re.IGNORECASE)
    # Strip HTML tags
    clean = re.sub(r"<[^>]+>", " ", clean)
    clean = re.sub(r"&nbsp;", " ", clean)
    clean = re.sub(r"&amp;", "&", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    print("BODY   :")
    print(clean[:3000])
    print("=" * 80)
