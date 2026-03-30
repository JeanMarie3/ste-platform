# Development rebuild script
# Stops the dev environment, compiles backend, builds frontend, and restarts

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "STE Platform - Development Rebuild" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Stop the dev environment
Write-Host "Step 1/4: Stopping dev environment..." -ForegroundColor Yellow
try {
    Set-Location "C:\Users\Jean001\source\ste-platform"
    & .\scripts\dev-stop.ps1
    Write-Host "✓ Dev environment stopped" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to stop dev environment: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 2: Compile backend Python
Write-Host "Step 2/4: Compiling backend Python code..." -ForegroundColor Yellow
try {
    Set-Location "C:\Users\Jean001\source\ste-platform\backend"
    python -m compileall app
    Write-Host "✓ Backend Python compilation completed" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to compile backend: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 3: Build frontend
Write-Host "Step 3/4: Building frontend..." -ForegroundColor Yellow
try {
    Set-Location "C:\Users\Jean001\source\ste-platform\frontend"
    npm run build
    Write-Host "✓ Frontend build completed" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to build frontend: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 4: Start the dev environment
Write-Host "Step 4/4: Starting dev environment..." -ForegroundColor Yellow
try {
    Set-Location "C:\Users\Jean001\source\ste-platform"
    & .\scripts\dev-up.ps1 -NoInstall
    Write-Host "✓ Dev environment started" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to start dev environment: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✓ Development rebuild completed successfully!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

