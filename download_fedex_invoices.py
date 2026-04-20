"""
Download FedEx invoice PDFs from Gmail (damoncollective@gmail.com) via IMAP.

SETUP (one-time):
1. Go to: https://myaccount.google.com/apppasswords
2. Create an App Password for "Mail"
3. Enter it when prompted (no spaces)
"""

import imaplib
import email
import os
import getpass
from datetime import datetime, timedelta

GMAIL_USER = "damoncollective@gmail.com"
DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
SEARCH_FROM = "GRinvoicequery@fedex.com"

IMAP_DATE_FMT = "%d-%b-%Y"   # e.g. 28-Mar-2026
INPUT_FORMATS = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d %b %Y", "%d %B %Y"]

PRESETS = [
    ("Last 30 days",  lambda: datetime.today() - timedelta(days=30)),
    ("Last 3 months", lambda: datetime.today() - timedelta(days=90)),
    ("Last 6 months", lambda: datetime.today() - timedelta(days=180)),
    ("This year",     lambda: datetime(datetime.today().year, 1, 1)),
    ("Last year",     lambda: datetime(datetime.today().year - 1, 1, 1)),
    ("All invoices",  lambda: datetime(2020, 1, 1)),
    ("Custom range",  None),
]


def parse_date(text):
    text = text.strip()
    for fmt in INPUT_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def ask_dates():
    print("\nSelect date range for FedEx invoices:")
    print("-" * 40)
    for i, (label, _) in enumerate(PRESETS, 1):
        print(f"  {i}. {label}")
    print("-" * 40)

    while True:
        choice = input("Enter option number: ").strip()
        if not choice.isdigit() or not (1 <= int(choice) <= len(PRESETS)):
            print("  Please enter a number from the list.")
            continue
        idx = int(choice) - 1
        label, fn = PRESETS[idx]
        break

    today = datetime.today()

    if fn is not None:
        since = fn()
        before = today + timedelta(days=1)
        print(f"  Range: {since.strftime('%d %b %Y')} → {today.strftime('%d %b %Y')}")
    else:
        print("\nEnter dates in DD/MM/YYYY format (e.g. 28/03/2026)")
        while True:
            since_str = input("  From date: ").strip()
            since = parse_date(since_str)
            if since:
                break
            print("  Could not read that date. Try DD/MM/YYYY.")

        before_str = input("  Until date (leave blank for today): ").strip()
        if before_str:
            before = parse_date(before_str)
            if not before:
                print("  Could not read end date, using today.")
                before = today
            before = before + timedelta(days=1)
        else:
            before = today + timedelta(days=1)

    return since, before


def connect(app_password):
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(GMAIL_USER, app_password)
    return mail


def fetch_invoice_ids(mail, since, before):
    mail.select("inbox")
    since_str = since.strftime(IMAP_DATE_FMT)
    before_str = before.strftime(IMAP_DATE_FMT)
    status, data = mail.search(
        None,
        f'(FROM "{SEARCH_FROM}" SINCE "{since_str}" BEFORE "{before_str}")'
    )
    if status != "OK":
        return []
    ids = data[0].split()
    return ids


def download_attachments(mail, msg_id, download_dir):
    status, data = mail.fetch(msg_id, "(RFC822)")
    if status != "OK":
        return []

    msg = email.message_from_bytes(data[0][1])
    subject = msg.get("Subject", "no subject")
    date_str = msg.get("Date", "")
    print(f"\n  [{date_str[:16]}]  {subject}")

    saved = []
    for part in msg.walk():
        if part.get_content_maintype() == "multipart":
            continue
        if part.get("Content-Disposition") is None:
            continue
        filename = part.get_filename()
        if not filename or not filename.lower().endswith(".pdf"):
            continue

        filepath = os.path.join(download_dir, filename)
        if os.path.exists(filepath):
            base, ext = os.path.splitext(filename)
            filepath = os.path.join(download_dir, f"{base}_dup{ext}")

        with open(filepath, "wb") as f:
            f.write(part.get_payload(decode=True))

        print(f"    Saved → {filepath}")
        saved.append(filepath)

    if not saved:
        print("    (no PDF attachment found)")

    return saved


def main():
    print("=" * 50)
    print("  FedEx Invoice Downloader")
    print(f"  Account : {GMAIL_USER}")
    print(f"  Save to : {DOWNLOAD_DIR}")
    print("=" * 50)

    since, before = ask_dates()

    app_password = getpass.getpass("\nGmail App Password: ")
    app_password = app_password.replace(" ", "")

    print("\nConnecting to Gmail...")
    try:
        mail = connect(app_password)
    except imaplib.IMAP4.error as e:
        print(f"\nLogin failed: {e}")
        print("Make sure you used a Gmail App Password from:")
        print("  https://myaccount.google.com/apppasswords")
        return

    print("Connected.")
    msg_ids = fetch_invoice_ids(mail, since, before)

    if not msg_ids:
        print("\nNo FedEx invoice emails found in that date range.")
        mail.logout()
        return

    print(f"\nFound {len(msg_ids)} invoice email(s). Downloading attachments...")

    all_saved = []
    for mid in msg_ids:
        saved = download_attachments(mail, mid, DOWNLOAD_DIR)
        all_saved.extend(saved)

    mail.logout()

    print("\n" + "=" * 50)
    if all_saved:
        print(f"Done. {len(all_saved)} PDF(s) saved to:")
        print(f"  {DOWNLOAD_DIR}")
        print("\nTip: run find_fedex_invoice.py to search inside them.")
    else:
        print("No PDFs were saved.")


if __name__ == "__main__":
    main()
