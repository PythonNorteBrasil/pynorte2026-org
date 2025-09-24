#!/usr/bin/env python3

import os
import httpx
import html

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
ISSUE_LABELS  = os.getenv("ISSUE_LABELS")

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

message_thread_id = THREADS_MAP.get(ISSUE_LABELS, 27)

def esc(s: str) -> str:
    return html.escape(s or "")

labels_list = [l.strip() for l in ISSUE_LABELS.split(",") if l.strip()]
labels_str = ", ".join(labels_list) if labels_list else "—"

MAX_BODY_CHARS = 700

body_preview = ISSUE_BODY[:MAX_BODY_CHARS]
if len(ISSUE_BODY) > MAX_BODY_CHARS:
    body_preview += "…"

final_message = (
    f"<b>🧩 Issue:</b> #{esc(ISSUE_NUMBER)} — {esc(ISSUE_TITLE)}\n"
    f"<b>👤 Autor:</b> {esc(ISSUE_USER)}\n"
    f"<b>🏷️ Labels:</b> {esc(labels_str)}\n"
    + (f"<b>🗒️ Evento:</b> {esc(ISSUER_MESSAGE)}\n" if ISSUER_MESSAGE else "")
    + (f"<b>🔗 Link:</b> <a href=\"{esc(ISSUE_URL)}\">{esc(ISSUE_URL)}</a>\n" if ISSUE_URL else "")
    + ("\n<b>📝 Descrição</b>\n<pre>"
       f"{esc(body_preview)}</pre>" if body_preview else "")
)

payload = {
    "chat_id": TELEGRAM_CHAT_ID,
    "text": final_message,
    "parse_mode": "HTML",
    "disable_web_page_preview": True,
    "message_thread_id": message_thread_id
}

with httpx.Client(timeout=20.0, follow_redirects=True) as client:
    resp = client.post(API_URL, data=payload)

    ctype = resp.headers.get("content-type", "")

    data = resp.json() if ctype.startswith("application/json") else {"raw": resp.text}
