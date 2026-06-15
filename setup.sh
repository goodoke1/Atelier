#!/usr/bin/env bash
#
# Atelier — one-command setup.
#
#   ./setup.sh                Interactive: choose provider / key, then launch.
#   ./setup.sh --demo         No key needed; runs the offline stub classifier.
#   ./setup.sh --key sk-...   Non-interactive with an Anthropic key.
#   ./setup.sh --down         Stop and remove the running stack.
#
# It writes .env (if missing), builds the images, and brings the stack up with
# Docker Compose. Open http://localhost:3000 when it finishes.

set -euo pipefail

cd "$(dirname "$0")"

# ── pretty output ───────────────────────────────────────────────
bold=$'\033[1m'; dim=$'\033[2m'; green=$'\033[32m'; red=$'\033[31m'; reset=$'\033[0m'
say()  { printf "%s\n" "$*"; }
ok()   { printf "${green}✓${reset} %s\n" "$*"; }
warn() { printf "${red}!${reset} %s\n" "$*"; }
rule() { printf "${dim}────────────────────────────────────────────────────────${reset}\n"; }

WEB_PORT="${WEB_PORT:-3000}"

# ── parse args ──────────────────────────────────────────────────
MODE="interactive"
CLI_KEY=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --demo) MODE="demo"; shift ;;
    --key) CLI_KEY="${2:-}"; MODE="key"; shift 2 ;;
    --down) MODE="down"; shift ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) warn "Unknown option: $1"; exit 1 ;;
  esac
done

# ── locate docker compose ───────────────────────────────────────
if docker compose version >/dev/null 2>&1; then
  DC="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  DC="docker-compose"
else
  warn "Docker Compose not found. Install Docker Desktop: https://docs.docker.com/get-docker/"
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  warn "Docker daemon isn't running. Start Docker Desktop and re-run ./setup.sh"
  exit 1
fi

# ── teardown shortcut ───────────────────────────────────────────
if [[ "$MODE" == "down" ]]; then
  rule; say "${bold}Stopping Atelier…${reset}"
  $DC down
  ok "Stopped."
  exit 0
fi

clear || true
rule
say "${bold}  A T E L I E R${reset}  ${dim}· fashion inspiration library${reset}"
rule

# ── build .env ──────────────────────────────────────────────────
write_env() {
  local provider="$1" key="$2" stub="$3"
  cp .env.example .env
  # portable in-place sed (BSD/macOS + GNU)
  sed -i.bak "s|^MODEL_PROVIDER=.*|MODEL_PROVIDER=${provider}|" .env
  sed -i.bak "s|^ANTHROPIC_API_KEY=.*|ANTHROPIC_API_KEY=${key}|" .env
  sed -i.bak "s|^FASHION_AI_STUB=.*|FASHION_AI_STUB=${stub}|" .env
  sed -i.bak "s|^WEB_PORT=.*|WEB_PORT=${WEB_PORT}|" .env
  rm -f .env.bak
}

if [[ -f .env ]]; then
  ok "Using existing .env (delete it to reconfigure)."
else
  case "$MODE" in
    demo)
      write_env "claude" "" "1"
      ok "Demo mode — offline stub classifier, no API key needed."
      ;;
    key)
      write_env "claude" "$CLI_KEY" ""
      ok "Configured Claude with the provided key."
      ;;
    interactive)
      say ""
      say "Choose how to classify images:"
      say "  ${bold}1${reset}) Claude (Anthropic) — best quality ${dim}(needs an API key)${reset}"
      say "  ${bold}2${reset}) Demo / offline     — no key, fake but functional classifier"
      say ""
      printf "Selection [1]: "
      read -r choice </dev/tty || choice="1"
      choice="${choice:-1}"
      if [[ "$choice" == "2" ]]; then
        write_env "claude" "" "1"
        ok "Demo mode — offline stub classifier."
      else
        printf "Paste your ANTHROPIC_API_KEY (input hidden): "
        read -rs apikey </dev/tty || apikey=""
        echo
        if [[ -z "$apikey" ]]; then
          warn "No key entered — falling back to demo mode."
          write_env "claude" "" "1"
        else
          write_env "claude" "$apikey" ""
          ok "Configured Claude."
        fi
      fi
      ;;
  esac
fi

# ── launch ──────────────────────────────────────────────────────
rule
say "${bold}Building & starting containers…${reset} ${dim}(first run pulls images; give it a minute)${reset}"
rule
$DC up --build -d

# ── wait for health ─────────────────────────────────────────────
printf "Waiting for the backend to become healthy "
for _ in $(seq 1 60); do
  if curl -fs "http://localhost:8000/api/health" >/dev/null 2>&1; then
    echo; ok "Backend is up."
    break
  fi
  printf "."
  sleep 2
done

rule
ok "Atelier is running."
say ""
say "   ${bold}Web app:${reset}  http://localhost:${WEB_PORT}"
say "   ${bold}API:${reset}      http://localhost:8000/api/health"
say ""
say "   ${dim}Logs:${reset}     ${DC} logs -f"
say "   ${dim}Stop:${reset}     ./setup.sh --down"
rule
