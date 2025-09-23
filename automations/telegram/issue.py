#!/usr/bin/env python3

import os
import httpx

API_BASE = "https://api.telegram.org"

TELEGRAM_TOKEN     = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")

ISSUE_TITLE        = os.getenv("ISSUE_TITLE")
ISSUER_MESSAGE     = os.getenv("MESSAGE")
ISSUE_NUMBER       = os.getenv("ISSUE_NUMBER")
ISSUE_URL          = os.getenv("ISSUE_URL")
ISSUE_USER         = os.getenv("ISSUE_USER")
ISSUE_REPO         = os.getenv("REPO")
ISSUE_BODY         = (os.getenv("ISSUE_BODY") or "").strip()
ISSUE_BODY_JSON  = os.getenv("ISSUE_BODY_JSON")

API_URL = f"{API_BASE}/bot{TELEGRAM_TOKEN}/sendMessage"

# Tópicos do grupo do Telegram

THREADS_MAP = {
    "CDC": 11,
    "Comunicação": 3,
    "Designer": 2,
    "Financeiro": 6,
    "Local": 9,
    "Logística": 0,
    "Palestrantes": 0,
    "Parcerias": 0,
    "Patrocínio": 4,
    "Site": 5
}

# Mapa de usuários github <> telegram

TELEGRAM_USERS_MAP = {}

message_thread_id = 27

final_message = f"""
labels: {ISSUE_BODY_JSON}
"""

payload = {
    "chat_id": TELEGRAM_CHAT_ID,
    "text": final_message,
    "parse_mode": "HTML",
    "disable_web_page_preview": True,
}

with httpx.Client(timeout=20.0, follow_redirects=True) as client:
    resp = client.post(API_URL, data=payload)

    ctype = resp.headers.get("content-type", "")

    data = resp.json() if ctype.startswith("application/json") else {"raw": resp.text}
