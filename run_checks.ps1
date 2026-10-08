Write-Host "Running AnalystIQ Test Suite..." -ForegroundColor Cyan

# Check if pytest is available, if not install it
if (-Not (Get-Command pytest -ErrorAction SilentlyContinue)) {
    Write-Host "Installing pytest..."
    pip install pytest
}

Write-Host "Running tests..."
python -m pytest tests/

if ($LASTEXITCODE -eq 0) {
    Write-Host "All tests passed successfully! ✅" -ForegroundColor Green
} else {
    Write-Host "Tests failed! ❌" -ForegroundColor Red
    exit 1
}
