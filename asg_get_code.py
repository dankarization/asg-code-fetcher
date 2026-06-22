#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


ENDPOINT = "https://webhook.asg.ge/Get24HourCodeEx.php"


def token_from_prefs(path: str) -> str:
    root = ET.parse(path).getroot()
    for item in root.findall("string"):
        if item.attrib.get("name") == "flutter.token" and item.text:
            return item.text.strip()
    raise SystemExit(f"flutter.token not found in {path}")


def env_required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"{name} is required")
    return value


def fetch_code(token: str, app_token: str | None = None) -> dict:
    app_token = app_token or env_required("ASG_APPLICATION_TOKEN")
    form = urllib.parse.urlencode(
        {
            "auth[application_token]": app_token,
            "data[TOKEN]": token,
        }
    ).encode()
    req = urllib.request.Request(
        ENDPOINT,
        data=form,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Dart/3.x (dart:io)",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch ASG 24-hour QR/code without emulator.")
    parser.add_argument("--token", help="ASG flutter.token value; can also be set as ASG_TOKEN")
    parser.add_argument("--app-token", help="ASG application_token value; can also be set as ASG_APPLICATION_TOKEN")
    parser.add_argument("--prefs", help="Path to FlutterSharedPreferences.xml")
    parser.add_argument("--raw", action="store_true", help="Print full JSON response")
    args = parser.parse_args()

    token = args.token or os.environ.get("ASG_TOKEN") or (token_from_prefs(args.prefs) if args.prefs else None)
    if not token:
        parser.error("pass --token, set ASG_TOKEN, or pass --prefs")

    app_token = args.app_token or os.environ.get("ASG_APPLICATION_TOKEN")
    data = fetch_code(token, app_token)
    if args.raw:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(data.get("codeRaw") or data.get("code") or "")
    return 0


if __name__ == "__main__":
    sys.exit(main())
