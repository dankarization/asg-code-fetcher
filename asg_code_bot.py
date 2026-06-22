#!/usr/bin/env python3
import argparse
import html
import json
import os
import sys
import time
import urllib.parse
import urllib.request

from asg_get_code import fetch_code


DEFAULT_RECIPIENTS = "5775112073,582043021"
MAIN_KEYBOARD = json.dumps(
    {
        "keyboard": [[{"text": "/code"}, {"text": "/qr"}]],
        "resize_keyboard": True,
        "is_persistent": True,
    }
)


def env_required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"{name} is required")
    return value


def recipient_ids() -> set[int]:
    raw = os.environ.get("RECIPIENT_IDS", DEFAULT_RECIPIENTS)
    ids = set()
    for item in raw.split(","):
        item = item.strip()
        if item:
            ids.add(int(item))
    return ids


def tg_request(bot_token: str, method: str, payload: dict, timeout: int = 30) -> dict:
    data = urllib.parse.urlencode(payload).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{bot_token}/{method}",
        data=data,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
    parsed = json.loads(body)
    if not parsed.get("ok"):
        raise RuntimeError(f"Telegram {method} failed: {body}")
    return parsed


def send_message(bot_token: str, chat_id: int, text: str, reply_markup: str | None = None) -> None:
    payload = {
        "chat_id": str(chat_id),
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    tg_request(
        bot_token,
        "sendMessage",
        payload,
    )


def expiry_markup(data: dict) -> str:
    expiry = data.get("expiry") or {}
    fallback = expiry.get("formatted") or expiry.get("iso") or "unknown"
    timestamp = expiry.get("timestamp")
    if timestamp:
        return f'<tg-time unix="{int(timestamp)}" format="dt">{html.escape(str(fallback))}</tg-time>'
    return html.escape(str(fallback))


def code_message(asg_token: str) -> str:
    data = fetch_code(asg_token)
    code = html.escape(str(data.get("codeRaw") or data.get("code") or "unknown"))
    return f"ASG lift code: <code>{code}</code>\nValid until: {expiry_markup(data)}"


def qr_message(asg_token: str) -> str:
    data = fetch_code(asg_token)
    qr = html.escape(str(data.get("qr") or "unknown"))
    return f"ASG QR: <code>{qr}</code>\nValid until: {expiry_markup(data)}"


def send_daily() -> int:
    bot_token = env_required("TELEGRAM_BOT_TOKEN")
    asg_token = env_required("ASG_TOKEN")
    text = code_message(asg_token)
    failures = 0
    for chat_id in sorted(recipient_ids()):
        try:
            send_message(bot_token, chat_id, text)
        except Exception as exc:
            failures += 1
            print(f"send failed for {chat_id}: {exc}", file=sys.stderr)
    return 1 if failures else 0


def handle_message(bot_token: str, asg_token: str, allowed: set[int], message: dict) -> None:
    chat = message.get("chat") or {}
    chat_id = int(chat.get("id"))
    text = (message.get("text") or "").strip()
    if chat_id not in allowed:
        return

    if text.startswith("/start"):
        send_message(
            bot_token,
            chat_id,
            "ASG lift bot is active. Use /code for the lift code or /qr for QR on demand.",
            MAIN_KEYBOARD,
        )
    elif text.startswith("/code") or text == "Code":
        send_message(bot_token, chat_id, code_message(asg_token), MAIN_KEYBOARD)
    elif text.startswith("/qr") or text in {"QR", "Qr", "qr"}:
        send_message(bot_token, chat_id, qr_message(asg_token), MAIN_KEYBOARD)


def poll() -> int:
    bot_token = env_required("TELEGRAM_BOT_TOKEN")
    asg_token = env_required("ASG_TOKEN")
    allowed = recipient_ids()
    offset = None
    while True:
        payload = {"timeout": "50"}
        if offset is not None:
            payload["offset"] = str(offset)
        try:
            result = tg_request(bot_token, "getUpdates", payload, timeout=65).get("result", [])
            for update in result:
                offset = int(update["update_id"]) + 1
                message = update.get("message")
                if message:
                    handle_message(bot_token, asg_token, allowed, message)
        except Exception as exc:
            print(f"poll error: {exc}", file=sys.stderr)
            time.sleep(5)


def main() -> int:
    parser = argparse.ArgumentParser(description="Telegram bot for ASG lift codes.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("send", help="Send current code to configured recipients")
    sub.add_parser("poll", help="Long-poll Telegram and answer /start, /code, and /qr")
    args = parser.parse_args()
    if args.command == "send":
        return send_daily()
    if args.command == "poll":
        return poll()
    return 2


if __name__ == "__main__":
    sys.exit(main())
