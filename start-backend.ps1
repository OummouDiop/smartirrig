# Script de démarrage du backend FastAPI
# Usage: .\start-backend.ps1

Write-Host "🚀 Démarrage du Backend FastAPI..." -ForegroundColor Green
Write-Host ""

# Changer vers le répertoire backend
Set-Location -Path "backend"

# Vérifier si uvicorn est installé
$uvicornExists = Get-Command uvicorn -ErrorAction SilentlyContinue

if (-not $uvicornExists) {
    Write-Host "❌ uvicorn n'est pas installé!" -ForegroundColor Red
    Write-Host "📦 Installation des dépendances..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

Write-Host "✅ Lancement du serveur sur http://localhost:8000" -ForegroundColor Green
Write-Host "📚 Documentation API: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Appuyez sur Ctrl+C pour arrêter le serveur" -ForegroundColor Yellow
Write-Host ""

# Démarrer le serveur
uvicorn main:app --reload --host 0.0.0.0 --port 8000
