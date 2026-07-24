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
    pnpm lint
    pnpm typecheck
    pnpm test
    pnpm build
    docker compose config --quiet
} finally {
    Pop-Location
}
