#!/usr/bin/env bash
# Enable Entra ID sign-in (Easy Auth) on the deployed web app — one command, one-time.
#
# ทำอะไร: สร้าง AAD app registration + เปิด App Service Authentication แบบ
# "Require authentication" — ทุก request ที่ยังไม่ login ถูก redirect ไป Microsoft login
# ก่อนถึง Gradio เสมอ (Gradio ไม่ต้องรู้เรื่อง auth เลย)
set -euo pipefail

RG="${RG:-gtm-pipeline-rg}"
APP="${APP:-gtm-deal-pipeline}"

TENANT=$(az account show --query tenantId -o tsv)
URL="https://$APP.azurewebsites.net"

echo "==> AAD app registration: $APP"
CLIENT_ID=$(az ad app create --display-name "$APP" \
  --web-redirect-uris "$URL/.auth/login/aad/callback" \
  --enable-id-token-issuance true \
  --query appId -o tsv)

echo "==> Client secret"
SECRET=$(az ad app credential reset --id "$CLIENT_ID" --display-name easyauth --query password -o tsv)

echo "==> Enable Easy Auth (require login) on $APP"
az webapp auth microsoft update -g "$RG" -n "$APP" \
  --client-id "$CLIENT_ID" --client-secret "$SECRET" \
  --issuer "https://login.microsoftonline.com/$TENANT/v2.0" -o none
az webapp auth update -g "$RG" -n "$APP" \
  --enabled true --action RedirectToLoginPage --redirect-provider azureActiveDirectory -o none

echo "==> Done — เปิด $URL จะเด้งไปหน้า Microsoft login ก่อนเสมอ"
