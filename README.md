# ASG Lift Code Fetcher

Small helper and Telegram bot for fetching ASG lift access codes from asg.ge without opening the slow mobile app every time.

It is useful when several people need the same daily lift code: configure the tokens once, run the bot, and let Telegram deliver daily notifications or answer `/code` on demand.

No AI or emulator is needed at runtime.

## Architecture

```mermaid
flowchart TD
    A[ASG mobile app login once] --> B[Extract flutter.token]
    B --> C[Local env: ASG_TOKEN]
    D[Local env: ASG_APPLICATION_TOKEN] --> E[asg_get_code.py]
    C --> E
    E --> F[asg.ge 24h code endpoint]
    F --> G[Current lift code + expiry]
    G --> H[asg_code_bot.py]
    H --> I[/code on demand]
    H --> J[systemd daily timer]
    H --> K[/qr on demand]
    I --> L[Allowed Telegram users]
    J --> L
    K --> L
```

Standalone Mermaid source: [`docs/architecture.mmd`](docs/architecture.mmd).

## Usage

Use a token directly:

```bash
ASG_APPLICATION_TOKEN='your-asg-application-token' \
ASG_TOKEN='your-flutter-token' \
./asg_get_code.py
```

Or pass it as an argument:

```bash
./asg_get_code.py \
  --app-token 'your-asg-application-token' \
  --token 'your-flutter-token'
```

Or read it from a dumped `FlutterSharedPreferences.xml`:

```bash
ASG_APPLICATION_TOKEN='your-asg-application-token' \
./asg_get_code.py --prefs FlutterSharedPreferences.xml --raw
```

Default output is only the current code:

```text
159544
```

`--raw` prints the full JSON response:

```json
{
  "status": 0,
  "message": "წარმატებული",
  "errorCode": "SUCCESS",
  "code": "159544",
  "codeRaw": "159544",
  "qr": "403229",
  "expiry": {
    "iso": "2026-06-22T16:21:02",
    "formatted": "22Jun, 16:21",
    "timestamp": 1782130862
  }
}
```

The code updates roughly once per day from the moment it is issued by ASG.

## Token Source

After logging into the ASG app once, pull app preferences from the debuggable build/emulator:

```bash
adb -s emulator-5558 shell run-as ge.asg.droid \
  cat /data/data/ge.asg.droid/shared_prefs/FlutterSharedPreferences.xml
```

Look for:

```xml
<string name="flutter.token">...</string>
```

Do not commit personal `flutter.token`, ASG application tokens, or Telegram bot tokens.

## Telegram Bot

The repository also includes a no-LLM Telegram bot runner:

- `/start` confirms the bot is active.
- `/code` sends the current ASG lift code on demand, without QR.
- `/qr` requests the QR code separately on demand.
- `asg_code_bot.py send` sends only the lift code to all configured recipients.
- `asg-code-daily.timer` sends only the lift code once per day.

Allowed default recipients:

```text
5775112073,582043021
```

Create a Telegram bot with BotFather, then configure:

```bash
mkdir -p ~/.config/asg-code-fetcher
cp env.example ~/.config/asg-code-fetcher/env
chmod 600 ~/.config/asg-code-fetcher/env
```

Edit `~/.config/asg-code-fetcher/env`:

```bash
TELEGRAM_BOT_TOKEN=123456789:botfather_token
ASG_APPLICATION_TOKEN=your-asg-application-token
ASG_TOKEN=your-flutter-token
RECIPIENT_IDS=5775112073,582043021
```

Install user systemd units:

```bash
./install_user_systemd.sh
systemctl --user enable --now asg-code-bot.service asg-code-daily.timer
```

Both recipients must open the bot in Telegram and send `/start` once. After that the daily sender can message them.

Manual checks:

```bash
systemctl --user start asg-code-daily.service
journalctl --user -u asg-code-bot.service -u asg-code-daily.service -n 100 --no-pager
```
