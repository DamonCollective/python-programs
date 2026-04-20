#!/usr/bin/env python3
"""
Search damoncollective@gmail.com for emails from Gisela Mayer in 2026
and download all attachments to ~/Documents/gisela_mayer_invoices_2026/
"""

import os
import base64

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.utils import parsedate_to_datetime

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE  = os.path.join(SCRIPT_DIR, "token_damoncollective.json")
SCOPES      = ["https://www.googleapis.com/auth/gmail.modify"]
OUTPUT_DIR  = os.path.expanduser("~/Documents/gisela_mayer_invoices_2026")

SEARCH_QUERY = 'from:gisela after:2025/12/31'

def get_service():
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build("gmail", "v1", credentials=creds)

def download_attachments(service, msg_id, date_str, subject, output_dir):
    msg = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
    saved = []

    def process_parts(parts):
        for part in parts:
            if "parts" in part:
                process_parts(part["parts"])
            filename = part.get("filename", "")
            body     = part.get("body", {})
            if filename and (body.get("attachmentId") or body.get("data")):
                # Build safe filename with date prefix
                safe_date = date_str.replace("/", "-")
                safe_name = f"{safe_date}_{filename}"
                out_path  = os.path.join(output_dir, safe_name)

                if body.get("attachmentId"):
                    att = service.users().messages().attachments().get(
                        userId="me", messageId=msg_id, id=body["attachmentId"]
                    ).execute()
                    data = base64.urlsafe_b64decode(att["data"] + "==")
                else:
                    data = base64.urlsafe_b64decode(body["data"] + "==")

                with open(out_path, "wb") as f:
                    f.write(data)
                saved.append(safe_name)
                print(f"    Saved: {safe_name}")

    if "parts" in msg["payload"]:
        process_parts(msg["payload"]["parts"])

    return saved

def main():
    print("Authenticating...")
    service = get_service()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Searching for Gisela Mayer emails in 2026...")
    all_messages = []
    page_token = None
    while True:
        params = {"userId": "me", "q": SEARCH_QUERY, "maxResults": 500}
        if page_token:
            params["pageToken"] = page_token
        response = service.users().messages().list(**params).execute()
        all_messages.extend(response.get("messages", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    print(f"Found {len(all_messages)} emails. Checking for attachments...")

    total_files = 0
    for msg_ref in all_messages:
        msg = service.users().messages().get(
            userId="me", id=msg_ref["id"], format="metadata",
            metadataHeaders=["From", "Subject", "Date"]
        ).execute()

        headers  = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        sender   = headers.get("From", "")
        subject  = headers.get("Subject", "")
        date_str = headers.get("Date", "")

        try:
            dt         = parsedate_to_datetime(date_str)
            email_date = dt.strftime("%Y-%m-%d")
            if dt.year != 2026:
                continue
        except Exception:
            email_date = "2026-00-00"

        print(f"  {email_date} | {sender[:50]} | {subject[:50]}")
        saved = download_attachments(service, msg_ref["id"], email_date, subject, OUTPUT_DIR)
        if not saved:
            print(f"    (no attachments)")
        total_files += len(saved)

    print(f"\nDone. {total_files} file(s) saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
