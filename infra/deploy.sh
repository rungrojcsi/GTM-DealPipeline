#!/usr/bin/env bash
# Deploy GTM Deal Pipeline (Gradio) to Azure App Service (Linux, code-based).
#
# Usage:
#   ./infra/deploy.sh                # create/update everything + zip deploy
#
# After first deploy (one-time, manual):
#   1) Set the Anthropic key (never commit it):
#      az webapp config appsettings set -g <RG> -n <APP> --settings ANTHROPIC_API_KEY=sk-ant-...
#   2) Enable Entra ID login (Easy Auth) — see infra/enable-auth.sh
set -euo pipefail

RG="${RG:-gtm-pipeline-rg}"
LOC="${LOC:-southeastasia}"
PLAN="${PLAN:-gtm-pipeline-plan}"
APP="${APP:-gtm-deal-pipeline}"          # ต้อง unique ทั่ว Azure (*.azurewebsites.net)
SKU="${SKU:-B1}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Resource group: $RG ($LOC)"
az group create -n "$RG" -l "$LOC" -o none

echo "==> App Service plan: $PLAN ($SKU, Linux)"
az appservice plan create -g "$RG" -n "$PLAN" --sku "$SKU" --is-linux -o none

echo "==> Web app: $APP (Python 3.12)"
az webapp create -g "$RG" -p "$PLAN" -n "$APP" --runtime "PYTHON:3.12" -o none

echo "==> App settings + startup command"
az webapp config appsettings set -g "$RG" -n "$APP" -o none --settings \
  SCM_DO_BUILD_DURING_DEPLOYMENT=true \
  DATA_DIR=/home/data \
  WEBSITES_CONTAINER_START_TIME_LIMIT=600
az webapp config set -g "$RG" -n "$APP" --startup-file "python app.py" -o none

# ล็อก 1 instance เสมอ — ข้อมูลเป็น CSV บน disk เครื่องเดียว ห้าม scale-out
az appservice plan update -g "$RG" -n "$PLAN" --number-of-workers 1 -o none

echo "==> Zip deploy (source build on Azure/Oryx)"
TMPZIP="$(mktemp -d)/app.zip"
(cd "$ROOT" && zip -q -r "$TMPZIP" \
  app.py render.py llm_utils.py scoring_agent.py discovery_agent.py \
  solution_shaping_agent.py solution_master.md requirements.txt)
az webapp deploy -g "$RG" -n "$APP" --src-path "$TMPZIP" --type zip -o none
rm -f "$TMPZIP"

echo "==> Done: https://$APP.azurewebsites.net"
echo "    (แอปจะยังขึ้น error จนกว่าจะตั้ง ANTHROPIC_API_KEY — ดูหัวไฟล์นี้)"
