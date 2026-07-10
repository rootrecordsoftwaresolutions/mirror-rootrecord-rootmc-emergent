# Dot-source from deploy scripts: . (Join-Path $repoRoot "scripts\load-env.ps1")

if (-not (Get-Command Import-DotEnvFile -ErrorAction SilentlyContinue)) {
    function Import-DotEnvFile([string]$LiteralPath, [switch]$SkipCloudflareKeys) {
        if (-not (Test-Path -LiteralPath $LiteralPath)) { return }
        Get-Content -LiteralPath $LiteralPath | ForEach-Object {
            $line = $_.Trim()
            if (-not $line -or $line.StartsWith("#")) { return }
            $p = $line.IndexOf("=")
            if ($p -gt 0) {
                $k = $line.Substring(0, $p).Trim()
                $v = $line.Substring($p + 1).Trim()
                if ($SkipCloudflareKeys -and $k -match '^CLOUDFLARE_|^ROOTMC_CLOUDFLARE_') { return }
                if ($k -and $v) { Set-Item -Path "Env:$k" -Value $v }
            }
        }
    }
}

$script:RepoRoot = if ($PSScriptRoot) {
    (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
} else {
    (Get-Location).Path
}
$script:RepoEnv = Join-Path $script:RepoRoot ".env"

Import-DotEnvFile $script:RepoEnv

Remove-Item Env:CLOUDFLARE_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:CLOUDFLARE_EMAIL -ErrorAction SilentlyContinue
