#!/usr/bin/env python3
"""
One-shot: download the Excel attachment from the Plistakas email,
save it to ~/Downloads/, then run forward_pending_invoices non-interactively.
"""

import os
import sys
import base64
import io
from unittest.mock import patch

# Change to alegro dir so credential paths resolve
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES     = ["https://www.googleapis.com/auth/gmail.modify"]
MESSAGE_ID = "19daaf4dff0bcc92"   # today's Plistakas email
RECIPIENT  = "damoncollective@gmail.com"
EXCEL_NAME = "ΔΑΜΩΝ ΕΚΚΡΕΜΟΤΗΤΕΣ ΠΑΡΑΣΤΑΤΙΚΩΝ.xlsx"

def get_service():
    token_file = "token_damoncollective.json"
    creds_file = "credentials_damoncollective.json"
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_file, "w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def download_excel(service):
    """Find and download the Excel attachment from the Plistakas message."""
    msg = service.users().messages().get(
        userId="me", id=MESSAGE_ID, format="full"
    ).execute()

    payload = msg.get("payload", {})

    def find_excel(parts):
        for part in parts:
            fname = part.get("filename", "")
            if fname.lower().endswith(".xlsx") or fname.lower().endswith(".xls"):
                att_id = part["body"].get("attachmentId")
                if att_id:
                    att  = service.users().messages().attachments().get(
                        userId="me", messageId=MESSAGE_ID, id=att_id
                    ).execute()
                    return fname, base64.urlsafe_b64decode(att["data"])
                else:
                    data = part["body"].get("data", "")
                    if data:
                        return fname, base64.urlsafe_b64decode(data)
            if "parts" in part:
                result = find_excel(part["parts"])
                if result:
                    return result
        return None

    parts = payload.get("parts", [payload])
    result = find_excel(parts)
    if not result:
        raise RuntimeError("No Excel attachment found in the message.")
    return result


def main():
    print("── Downloading Excel from Plistakas email ──")
    service = get_service()
    fname, data = download_excel(service)
    print(f"✓ Found attachment: {fname}  ({len(data):,} bytes)")

    save_path = os.path.join(os.path.expanduser("~"), "Downloads", EXCEL_NAME)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, "wb") as f:
        f.write(data)
    print(f"✓ Saved to: {save_path}")

    print("\n── Running forward_pending_invoices ──")
    # Patch stdin so the interactive prompts are answered automatically
    fake_input = io.StringIO(f"{RECIPIENT}\nyes\n")
    with patch("builtins.input", side_effect=lambda prompt="": (print(prompt, end=""), fake_input.readline().strip())[1]):
        import forward_pending_invoices
        forward_pending_invoices.main()


if __name__ == "__main__":
    main()
