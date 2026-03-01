# Script de vérification automatique de l'état des services
# Usage: .\check-services.ps1

Write-Host "🔍 Vérification de l'état des services Smart Irrigation" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Fonction pour tester un port
function Test-Port {
    param($Port, $ServiceName)
    try {
        $connection = Test-NetConnection -ComputerName localhost -Port $Port -InformationLevel Quiet -WarningAction SilentlyContinue
        if ($connection) {
            Write-Host "✅ $ServiceName (Port $Port): " -NoNewline -ForegroundColor Green
            Write-Host "ACTIF" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ $ServiceName (Port $Port): " -NoNewline -ForegroundColor Red
            Write-Host "INACTIF" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "❌ $ServiceName (Port $Port): " -NoNewline -ForegroundColor Red
        Write-Host "ERREUR" -ForegroundColor Red
        return $false
    }
}

# Vérifier Backend (Port 8000)
Write-Host "1️⃣  Backend FastAPI:" -ForegroundColor Yellow
$backendActive = Test-Port -Port 8000 -ServiceName "Backend API"

if ($backendActive) {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/" -Method Get -ErrorAction Stop
        Write-Host "   → Message: $($response.message)" -ForegroundColor Gray
    } catch {
        Write-Host "   → Erreur de connexion au backend" -ForegroundColor Red
    }
} else {
    Write-Host "   💡 Pour démarrer: cd backend; uvicorn main:app --reload" -ForegroundColor Yellow
}

Write-Host ""

# Vérifier Frontend (Port 3000)
Write-Host "2️⃣  Frontend React:" -ForegroundColor Yellow
$frontendActive = Test-Port -Port 3000 -ServiceName "Frontend React"

if (-not $frontendActive) {
    Write-Host "   💡 Pour démarrer: cd frontend_irrig; npm start" -ForegroundColor Yellow
}

Write-Host ""

# Tester la connexion API si les deux sont actifs
if ($backendActive -and $frontendActive) {
    Write-Host "3️⃣  Test de l'API:" -ForegroundColor Yellow
    try {
        $history = Invoke-RestMethod -Uri "http://localhost:8000/history?limit=1" -Method Get -ErrorAction Stop
        if ($history.Count -gt 0) {
            Write-Host "✅ Données capteurs disponibles" -ForegroundColor Green
            $data = $history[0]
            Write-Host "   → Température: $($data.temperature)°C" -ForegroundColor Gray
            Write-Host "   → Humidité air: $($data.humidity)%" -ForegroundColor Gray
            Write-Host "   → Humidité sol: $($data.soil_moisture)%" -ForegroundColor Gray
        } else {
            Write-Host "⚠️  Base de données vide" -ForegroundColor Yellow
            Write-Host "   💡 Lancez la simulation: cd simulation; python simulation_backend.py" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ Erreur lors de la récupération des données" -ForegroundColor Red
    }
    
    Write-Host ""
    
    # Vérifier l'état de la valve
    try {
        $valve = Invoke-RestMethod -Uri "http://localhost:8000/valve-state/zone_1" -Method Get -ErrorAction Stop
        $status = if ($valve.is_open) { "🟢 ACTIVE" } else { "🔴 INACTIVE" }
        Write-Host "✅ État de la pompe: $status" -ForegroundColor Green
    } catch {
        Write-Host "❌ Erreur lors de la vérification de la valve" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "📋 Résumé:" -ForegroundColor Cyan

if ($backendActive -and $frontendActive) {
    Write-Host "   🎉 Tous les services sont actifs!" -ForegroundColor Green
    Write-Host "   🌐 Dashboard: http://localhost:3000" -ForegroundColor Cyan
    Write-Host "   📚 API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host "   🧪 Test: Ouvrir test-connexion.html" -ForegroundColor Cyan
} elseif ($backendActive) {
    Write-Host "   ⚠️  Backend actif mais Frontend inactif" -ForegroundColor Yellow
    Write-Host "   💡 Démarrez le frontend: cd frontend_irrig; npm start" -ForegroundColor Yellow
} elseif ($frontendActive) {
    Write-Host "   ⚠️  Frontend actif mais Backend inactif" -ForegroundColor Yellow
    Write-Host "   💡 Démarrez le backend: cd backend; uvicorn main:app --reload" -ForegroundColor Yellow
} else {
    Write-Host "   ❌ Aucun service actif" -ForegroundColor Red
    Write-Host "   💡 Suivez le guide: QUICK_START.md" -ForegroundColor Yellow
}

Write-Host ""
