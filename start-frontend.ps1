# Script de démarrage du frontend React
# Usage: .\start-frontend.ps1

Write-Host "🎨 Démarrage du Frontend React..." -ForegroundColor Green
Write-Host ""

# Changer vers le répertoire frontend
Set-Location -Path "frontend_irrig"

# Vérifier si node_modules existe
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Installation des dépendances npm..." -ForegroundColor Yellow
    npm install
}

Write-Host "✅ Lancement de l'application sur http://localhost:3000" -ForegroundColor Green
Write-Host ""
Write-Host "Appuyez sur Ctrl+C pour arrêter l'application" -ForegroundColor Yellow
Write-Host ""

# Démarrer l'application React
npm start
