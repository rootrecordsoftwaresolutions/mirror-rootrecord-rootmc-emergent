# Cloudflare Pages deploy for the RootMC Terminal PWA.
# Attach app.rootmc.net: Cloudflare Dashboard > Pages > rootmc-app > Custom domains
# Preview: https://rootmc-app.pages.dev
# Deploy: powershell -File deploy.ps1
$ErrorActionPreference = "Stop"
$PrevNativeErr = $ErrorActionPreference

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
. (Join-Path $repoRoot "scripts\load-env.ps1")

if (-not $env:CLOUDFLARE_API_TOKEN -or $env:CLOUDFLARE_API_TOKEN.Length -lt 20) {
    throw "Set CLOUDFLARE_API_TOKEN in repo root .env"
}
if (-not $env:CLOUDFLARE_ACCOUNT_ID) {
    throw "Set CLOUDFLARE_ACCOUNT_ID in repo root .env"
}

Set-Location $PSScriptRoot

# Production build env — reads from .env if present, otherwise sets safe defaults.
# For live prod the Pages dashboard must ALSO set these under "Environment variables (Production)".
if (-not $env:REACT_APP_ROOTMC_API)   { $env:REACT_APP_ROOTMC_API   = "https://api.rootmc.net" }
if (-not $env:REACT_APP_USE_MOCK)     { $env:REACT_APP_USE_MOCK     = "false" }
if (-not $env:REACT_APP_DEMO_LINK)    { $env:REACT_APP_DEMO_LINK    = "false" }
# Do NOT default REACT_APP_LIVE_REWARDS=true — the human flips this only after
# api.rootmc.net exposes /app/checkin/* and /app/vote/* routes.
if (-not $env:REACT_APP_LIVE_REWARDS) { $env:REACT_APP_LIVE_REWARDS = "false" }

Write-Host "Building rootmc-app with:"
Write-Host "  REACT_APP_ROOTMC_API   = $env:REACT_APP_ROOTMC_API"
Write-Host "  REACT_APP_USE_MOCK     = $env:REACT_APP_USE_MOCK"
Write-Host "  REACT_APP_DEMO_LINK    = $env:REACT_APP_DEMO_LINK"
Write-Host "  REACT_APP_LIVE_REWARDS = $env:REACT_APP_LIVE_REWARDS"

# Install + build via yarn (matches this repo's package manager)
if (Test-Path "yarn.lock") {
    yarn install --frozen-lockfile 2>&1 | Out-Host
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    yarn build 2>&1 | Out-Host
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} else {
    npm ci 2>&1 | Out-Host
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    npm run build 2>&1 | Out-Host
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

$project = "rootmc-app"
Write-Host "Deploying Pages project $project to RootMC account ..."

$ErrorActionPreference = "Continue"
$projList = (npx wrangler pages project list 2>&1) | Out-String
$ErrorActionPreference = $PrevNativeErr
if ($projList -notmatch $project) {
    Write-Host "Creating Pages project $project ..."
    npx wrangler pages project create $project --production-branch main 2>&1 | Out-Host
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

$ErrorActionPreference = "Continue"
npx wrangler pages deploy build `
    --project-name $project `
    --branch main `
    --commit-dirty=true 2>&1 | Out-Host
$ErrorActionPreference = $PrevNativeErr
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Done. Attach custom domain app.rootmc.net in Cloudflare Dashboard: Pages > rootmc-app > Custom domains."
Write-Host "Reminder: only flip REACT_APP_LIVE_REWARDS=true after Worker routes /api/rootmc/app/checkin/* and /api/rootmc/app/vote/* are deployed on api.rootmc.net."
