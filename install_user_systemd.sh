#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_HOME="${HOME}/.local/share/asg-code-fetcher"
CONFIG_HOME="${HOME}/.config/asg-code-fetcher"
SYSTEMD_HOME="${HOME}/.config/systemd/user"

mkdir -p "$APP_HOME" "$CONFIG_HOME" "$SYSTEMD_HOME"
install -m 755 "$ROOT/asg_get_code.py" "$APP_HOME/asg_get_code.py"
install -m 755 "$ROOT/asg_code_bot.py" "$APP_HOME/asg_code_bot.py"
install -m 644 "$ROOT/systemd/asg-code-bot.service" "$SYSTEMD_HOME/asg-code-bot.service"
install -m 644 "$ROOT/systemd/asg-code-daily.service" "$SYSTEMD_HOME/asg-code-daily.service"
install -m 644 "$ROOT/systemd/asg-code-daily.timer" "$SYSTEMD_HOME/asg-code-daily.timer"

if [[ ! -f "$CONFIG_HOME/env" ]]; then
  install -m 600 "$ROOT/env.example" "$CONFIG_HOME/env"
  echo "Created $CONFIG_HOME/env; fill TELEGRAM_BOT_TOKEN, ASG_APPLICATION_TOKEN, and ASG_TOKEN before enabling services."
fi

systemctl --user daemon-reload
echo "Installed user units. Enable after configuring env:"
echo "  systemctl --user enable --now asg-code-bot.service asg-code-daily.timer"
