#!/usr/bin/env python3

import os
import sys
import html
import textwrap
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

message_thread_id = 27

final_message = """
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

def build_message() -> str:
    # Se MESSAGE estiver definido, usa direto
    direct = os.getenv("MESSAGE")
    if direct:
        return direct

    title   = os.getenv("ISSUE_TITLE")
    number  = os.getenv("ISSUE_NUMBER")
    url     = os.getenv("ISSUE_URL")
    user    = os.getenv("ISSUE_USER")
    repo    = os.getenv("REPO")
    body    = (os.getenv("ISSUE_BODY") or "").strip()
    labels  = os.getenv("ISSUE_LABELS_JSON")


    if any([title, number, url, user, repo, body]):
        if len(body) > 700:
            body = body[:700] + "…"
        esc = lambda s: html.escape(s or "")
        return textwrap.dedent(f"""
                               labels: {labels}</br>
        🆕 <b>Issue aberta</b> em <b>{esc(repo or '(repo?)')}</b>
        <b>#{esc(str(number or '?'))}</b>: {esc(title or '(sem título)')}
        👤 Autor: {esc(user or '?')}
        🔗 <a href="{esc(url or '')}">{esc(url or '')}</a>

        <b>Descrição</b>:
        {esc(body) if body else '(sem descrição)'}
        """).strip()

    # Fallback final
    return "hello"

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ Defina TELEGRAM_BOT_TOKEN no ambiente.")
        sys.exit(2)

    chat_id = os.getenv("TELEGRAM_CHAT_ID", "-1002597220683")

    thread_raw = 27
    try:
        message_thread_id = int(thread_raw) if thread_raw else 0
    except ValueError:
        message_thread_id = 0

    text = build_message()

    url = f"{API_BASE}/bot{token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if message_thread_id:
        payload["message_thread_id"] = message_thread_id

    with httpx.Client(timeout=20.0, follow_redirects=True) as client:
        resp = client.post(url, data=payload)
        # Tenta interpretar JSON; se falhar, mostra texto cru
        ctype = resp.headers.get("content-type", "")
        data = resp.json() if ctype.startswith("application/json") else {"raw": resp.text}

    if not resp.is_success or not data.get("ok", False):
        print("⚠️ Falha ao enviar mensagem para o Telegram.")
        print("Status:", resp.status_code)
        print("Resposta:", data)
        sys.exit(1)

    result = data.get("result", {})
    print("✅ Mensagem enviada com sucesso!")
    print("chat_id:", result.get("chat", {}).get("id"))
    print("message_id:", result.get("message_id"))

if __name__ == "__main__":
    main()
