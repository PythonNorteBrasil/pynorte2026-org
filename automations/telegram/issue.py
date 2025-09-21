#!/usr/bin/env python3
# automations/telegram/issue.py
# Envia uma notificação para o Telegram usando httpx.
# Variáveis de ambiente suportadas:
# - TELEGRAM_BOT_TOKEN (obrigatório)
# - TELEGRAM_CHAT_ID (default: -1002597220683)
# - TELEGRAM_THREAD_ID (default: 6; use vazio para não enviar em thread)
# - MESSAGE (opcional; se presente, é usada como mensagem base)
# - APPEND_LABELS_TO_MESSAGE ("true"/"1" para anexar labels ao MESSAGE)
#
# Para montar mensagens automaticamente a partir de dados da issue:
# - ISSUE_TITLE, ISSUE_NUMBER, ISSUE_URL, ISSUE_USER, ISSUE_BODY, REPO
# - ISSUE_LABELS (opcional: CSV "bug,help wanted" ou JSON
#   '["bug","help wanted"]' ou '[{"name":"bug"},{"name":"help wanted"}]')
#
# Se ISSUE_LABELS não for informado, o script tenta ler labels do payload
# do GitHub Actions via GITHUB_EVENT_PATH.

import os
import sys
import html
import textwrap
import json
import httpx
from typing import List, Any

API_BASE = "https://api.telegram.org"

def _as_bool(val: str | None) -> bool:
    return str(val).lower() in {"1", "true", "yes", "y"}

def _escape(s: str | None) -> str:
    return html.escape(s or "")

def _from_env_issue_labels() -> List[str]:
    raw = os.getenv("ISSUE_LABELS")
    if not raw:
        return []
    # Tenta JSON primeiro
    try:
        data: Any = json.loads(raw)
        if isinstance(data, list):
            names: List[str] = []
            for item in data:
                if isinstance(item, str):
                    names.append(item)
                elif isinstance(item, dict) and "name" in item:
                    names.append(str(item["name"]))
            return [n for n in (x.strip() for x in names) if n]
    except json.JSONDecodeError:
        pass

    # CSV simples
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return parts

def _from_event_payload_labels() -> List[str]:
    """Lê labels do arquivo JSON do evento do GitHub (GITHUB_EVENT_PATH)."""
    path = os.getenv("GITHUB_EVENT_PATH")
    if not path or not os.path.isfile(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        issue = payload.get("issue") or {}
        labels = issue.get("labels") or []
        names: List[str] = []
        for lb in labels:
            if isinstance(lb, dict) and "name" in lb:
                names.append(str(lb["name"]))
            elif isinstance(lb, str):
                names.append(lb)
        return [n for n in (x.strip() for x in names) if n]
    except Exception:
        return []

def get_issue_labels() -> List[str]:
    # 1) via env ISSUE_LABELS (CSV/JSON)
    labels = _from_env_issue_labels()
    if labels:
        return labels
    # 2) via payload do evento
    labels = _from_event_payload_labels()
    return labels

def _labels_line() -> str:
    labels = get_issue_labels()
    if not labels:
        return "🏷️ Labels: (nenhum)"
    # Evita mensagens gigantes: limita a ~10 labels
    MAX = 10
    listed = labels[:MAX]
    suffix = " …" if len(labels) > MAX else ""
    return f"🏷️ Labels: {', '.join(_escape(x) for x in listed)}{suffix}"

def build_message() -> str:
    # Se MESSAGE estiver definido, usa direto (com opção de anexar labels)
    direct = os.getenv("MESSAGE")
    if direct:
        if _as_bool(os.getenv("APPEND_LABELS_TO_MESSAGE")):
            return f"{direct}\n\n{_labels_line()}"
        return direct

    # Caso contrário, tenta montar com dados de issue (se existirem)
    title   = os.getenv("ISSUE_TITLE")
    number  = os.getenv("ISSUE_NUMBER")
    url     = os.getenv("ISSUE_URL")
    user    = os.getenv("ISSUE_USER")
    repo    = os.getenv("REPO")
    body    = (os.getenv("ISSUE_BODY") or "").strip()

    if any([title, number, url, user, repo, body]):
        if len(body) > 700:
            body = body[:700] + "…"
        labels_line = _labels_line()
        return textwrap.dedent(f"""
        🆕 <b>Issue</b> em <b>{_escape(repo or '(repo?)')}</b>
        <b>#{_escape(str(number or '?'))}</b>: {_escape(title or '(sem título)')}
        👤 Autor: {_escape(user or '?')}
        {labels_line}
        🔗 <a href="{_escape(url or '')}">{_escape(url or '')}</a>

        <b>Descrição</b>:
        {_escape(body) if body else '(sem descrição)'}
        """).strip()

    # Fallback final
    return "hello"

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ Defina TELEGRAM_BOT_TOKEN no ambiente.")
        sys.exit(2)

    chat_id = os.getenv("TELEGRAM_CHAT_ID", "-1002597220683")
    thread_raw = os.getenv("TELEGRAM_THREAD_ID", "6")
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
