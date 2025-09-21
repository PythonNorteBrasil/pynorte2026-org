#!/usr/bin/env python3
# scripts/test_telegram_httpx.py
# Envia uma notificação para o Telegram usando httpx.
# Requer as variáveis de ambiente: TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID

import httpx
import os

API_BASE = "https://api.telegram.org"

token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = "-1002597220683"

url = f"{API_BASE}/bot{token}/sendMessage"
payload = {
    "chat_id": chat_id,
    "text": "hello",
    "parse_mode": "HTML",
    "disable_web_page_preview": True,
    "message_thread_id": 6
}
with httpx.Client(timeout=20.0, follow_redirects=True) as client:
    resp = client.post(url, data=payload)
    data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
    print(data)