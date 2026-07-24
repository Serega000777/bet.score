$ErrorActionPreference = 'Stop'

Push-Location "$PSScriptRoot\..\backend"
try {
    ruff format --check --no-cache .
    ruff check --no-cache .
    mypy --cache-dir "$env:TEMP\bet-score-mypy" src
    pytest
} finally {
    Pop-Location
}

Push-Location "$PSScriptRoot\.."
try {
    corepack pnpm@10.13.1 --filter './frontend' --filter './telegram-mini-app' lint
    corepack pnpm@10.13.1 --filter './frontend' --filter './telegram-mini-app' typecheck
    corepack pnpm@10.13.1 --filter './frontend' --filter './telegram-mini-app' test
    corepack pnpm@10.13.1 --filter './frontend' --filter './telegram-mini-app' build
    docker compose config --quiet
} finally {
    Pop-Location
}
