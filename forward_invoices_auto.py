#!/usr/bin/env python3
"""
Automated (non-interactive) version of forward_invoices.py.
Runs on the 10th of each month via cron.
Searches last month's foreign supplier invoices and sends to TO_EMAIL.
"""

import os
import sys
import base64
import datetime
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# ── CONFIG ──────────────────────────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

ACCOUNTS = [
    {
        "email":      "damoncollective@gmail.com",
        "creds_file": os.path.join(SCRIPT_DIR, "credentials_damoncollective.json"),
        "token_file": os.path.join(SCRIPT_DIR, "token_damoncollective.json"),
    },
    {
        "email":      "wigscoop@gmail.com",
        "creds_file": os.path.join(SCRIPT_DIR, "credentials_damoncollective.json"),
        "token_file": os.path.join(SCRIPT_DIR, "token_wigscoop.json"),
    },
]

SENDING_ACCOUNT_INDEX = 0

SENDER   = "info@damoncoop.eu"
CC       = "info@damoncoop.eu"
TO_EMAIL = "costaspapapa@gmail.com"
SCOPES   = ["https://www.googleapis.com/auth/gmail.modify"]

LOG_FILE = os.path.join(SCRIPT_DIR, "forward_invoices_auto.log")

INVOICE_KEYWORDS = [
    "invoice", "factura", "fattura", "bill", "receipt",
    "payment due", "pro forma", "proforma", "statement of account",
]

EXCLUDE_SENDERS = [
    "alegro.gr", "damoncoop.eu", "claireswigs.com",
    "damoncollective@gmail.com", "wigscoop@gmail.com",
    "paypal.com",
]

EXCLUDE_SUBJECT_KEYWORDS = [
    "saldo", "bonifico", "your invoice to", "paid for your invoice",
    "we sent your invoice", "reminder from",
]

REQUIRE_ATTACHMENT = True

EXCLUDE_ATTACHMENT_MIMES = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp", "image/tiff"}
EXCLUDE_ATTACHMENT_EXTS  = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif"}

ATTACHMENT_EXEMPT_SENDERS = [
    "payments-noreply@google.com",
]

# ────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
)
log = logging.getLogger(__name__)


def get_month_range():
    """Return (after, before) for the previous calendar month."""
    today            = datetime.date.today()
    first_this_month = today.replace(day=1)
    last_month_end   = first_this_month - datetime.timedelta(days=1)
    month_start      = last_month_end.replace(day=1)
    return (
        month_start.strftime("%Y/%m/%d"),
        first_this_month.strftime("%Y/%m/%d"),
    )


def get_subject(after):
    """Build subject with the month name in Greek."""
    MONTHS_GR = [
        "", "Ιανουάριος", "Φεβρουάριος", "Μάρτιος", "Απρίλιος",
        "Μάιος", "Ιούνιος", "Ιούλιος", "Αύγουστος",
        "Σεπτέμβριος", "Οκτώβριος", "Νοέμβριος", "Δεκέμβριος",
    ]
    d = datetime.datetime.strptime(after, "%Y/%m/%d")
    return f"Τιμολόγια εξωτερικού — {MONTHS_GR[d.month]} {d.year}"


def get_service(account: dict):
    creds = None
    if os.path.exists(account["token_file"]):
        creds = Credentials.from_authorized_user_file(account["token_file"], SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise RuntimeError(
                f"Token missing or expired for {account['email']} and no browser available. "
                f"Run forward_invoices.py manually once to re-authenticate."
            )
        with open(account["token_file"], "w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def extract_header(headers, name):
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def decode_part(part):
    data = part["body"].get("data", "")
    return base64.urlsafe_b64decode(data) if data else b""


def get_attachments_and_body(service, msg):
    attachments = []
    body_text   = ""
    payload     = msg.get("payload", {})

    def walk(parts):
        nonlocal body_text
        for part in parts:
            mime     = part.get("mimeType", "")
            filename = part.get("filename", "")
            if filename:
                ext = os.path.splitext(filename.lower())[1]
                if mime not in EXCLUDE_ATTACHMENT_MIMES and ext not in EXCLUDE_ATTACHMENT_EXTS:
                    att_id = part["body"].get("attachmentId")
                    if att_id:
                        att  = service.users().messages().attachments().get(
                            userId="me", messageId=msg["id"], id=att_id
                        ).execute()
                        data = base64.urlsafe_b64decode(att["data"])
                    else:
                        data = decode_part(part)
                    attachments.append((filename, data))
            elif mime == "text/plain" and not body_text:
                body_text = decode_part(part).decode("utf-8", errors="ignore")
            if "parts" in part:
                walk(part["parts"])

    if "parts" in payload:
        walk(payload["parts"])
    elif payload.get("mimeType") == "text/plain":
        body_text = decode_part(payload).decode("utf-8", errors="ignore")

    return attachments, body_text


def has_real_attachment(msg):
    payload = msg.get("payload", {})
    def walk(parts):
        for part in parts:
            filename = part.get("filename", "")
            mime     = part.get("mimeType", "")
            if filename and not mime.startswith("text/"):
                ext = os.path.splitext(filename.lower())[1]
                if mime not in EXCLUDE_ATTACHMENT_MIMES and ext not in EXCLUDE_ATTACHMENT_EXTS:
                    return True
            if "parts" in part and walk(part["parts"]):
                return True
        return False
    return walk(payload.get("parts", []))


def is_invoice_email(msg):
    headers  = msg["payload"].get("headers", [])
    subject  = extract_header(headers, "subject").lower()
    snippet  = msg.get("snippet", "").lower()
    combined = subject + " " + snippet
    if any(kw in subject for kw in EXCLUDE_SUBJECT_KEYWORDS):
        return False
    if REQUIRE_ATTACHMENT and not has_real_attachment(msg):
        sender = extract_header(headers, "from").lower()
        if not any(ex in sender for ex in ATTACHMENT_EXEMPT_SENDERS):
            return False
    return any(kw in combined for kw in INVOICE_KEYWORDS)


def build_query(after, before):
    keyword_part = " OR ".join(f'"{kw}"' for kw in INVOICE_KEYWORDS)
    exclude_part = " ".join(f"-from:{d}" for d in EXCLUDE_SENDERS)
    return f"after:{after} before:{before} ({keyword_part}) {exclude_part}"


def search_account(account: dict, query: str):
    log.info(f"Searching {account['email']}...")
    service  = get_service(account)
    results  = service.users().messages().list(
        userId="me", q=query, maxResults=100
    ).execute()
    messages = results.get("messages", [])
    log.info(f"  {len(messages)} messages found, filtering...")

    invoices = []
    for m in messages:
        msg = service.users().messages().get(
            userId="me", id=m["id"], format="full"
        ).execute()
        if not is_invoice_email(msg):
            continue
        headers      = msg["payload"].get("headers", [])
        orig_from    = extract_header(headers, "from")
        orig_subject = extract_header(headers, "subject")
        attachments, body_text = get_attachments_and_body(service, msg)
        invoices.append({
            "account":     account["email"],
            "from":        orig_from,
            "subject":     orig_subject,
            "attachments": attachments,
            "body":        body_text,
        })

    log.info(f"  {len(invoices)} invoices identified")
    return invoices


def main():
    log.info("=== forward_invoices_auto.py started ===")

    after, before = get_month_range()
    subject       = get_subject(after)
    query         = build_query(after, before)
    log.info(f"Period: {after} → {before}")

    all_invoices = []
    for account in ACCOUNTS:
        try:
            found = search_account(account, query)
            all_invoices.extend(found)
        except Exception as e:
            log.error(f"Account {account['email']} failed: {e}")

    if not all_invoices:
        log.info("No invoices found. Nothing sent.")
        return

    # Build outgoing email
    outer_msg = MIMEMultipart()
    outer_msg["From"]    = SENDER
    outer_msg["To"]      = TO_EMAIL
    outer_msg["Cc"]      = CC
    outer_msg["Subject"] = subject

    summary_lines = [
        f"Τιμολόγια εξωτερικού — {after} έως {before}",
        "",
    ]

    attachment_count = 0
    for i, inv in enumerate(all_invoices, 1):
        summary_lines.append(f"{i}. Από: {inv['from']}")
        summary_lines.append(f"   Θέμα: {inv['subject']}")
        summary_lines.append(f"   Γραμματοκιβώτιο: {inv['account']}")

        if inv["attachments"]:
            names = []
            for filename, data in inv["attachments"]:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(data)
                encoders.encode_base64(part)
                safe_name = f"{i:02d}_{filename}"
                part.add_header("Content-Disposition", "attachment", filename=safe_name)
                outer_msg.attach(part)
                names.append(safe_name)
                attachment_count += 1
            summary_lines.append(f"   Αρχεία: {', '.join(names)}")
        else:
            text_part = MIMEBase("text", "plain")
            content   = f"From: {inv['from']}\nSubject: {inv['subject']}\n\n{inv['body']}"
            text_part.set_payload(content.encode("utf-8"))
            encoders.encode_base64(text_part)
            safe_name = f"{i:02d}_invoice_body.txt"
            text_part.add_header("Content-Disposition", "attachment", filename=safe_name)
            outer_msg.attach(text_part)
            attachment_count += 1
            summary_lines.append("   (χωρίς συνημμένο — επισυνάπτεται το κείμενο)")

        summary_lines.append("")

    outer_msg.attach(MIMEText("\n".join(summary_lines), "plain", "utf-8"))

    sending_service = get_service(ACCOUNTS[SENDING_ACCOUNT_INDEX])
    raw = base64.urlsafe_b64encode(outer_msg.as_bytes()).decode("utf-8")
    sending_service.users().messages().send(
        userId="me", body={"raw": raw}
    ).execute()

    log.info(f"Sent successfully: {len(all_invoices)} invoices, {attachment_count} attachments → {TO_EMAIL}")
    log.info("=== done ===")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.exception(f"Fatal error: {e}")
        sys.exit(1)
