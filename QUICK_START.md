# 🚀 Guide de Démarrage Rapide - Smart Irrigation System

## Démarrer le système complet en 3 étapes

### Étape 1️⃣ : Démarrer le Backend (dans un terminal)

```powershell
cd C:\diengsalaa\Supnum_L3_S5\irraga\smartirrig
.\start-backend.ps1
```

**OU manuellement:**
```powershell
cd backend
uvicorn main:app --reload
```

✅ Le backend sera accessible sur: `http://localhost:8000`
📚 Documentation API: `http://localhost:8000/docs`

---

### Étape 2️⃣ : Démarrer le Frontend (dans un nouveau terminal)

```powershell
cd C:\diengsalaa\Supnum_L3_S5\irraga\smartirrig
.\start-frontend.ps1
```

**OU manuellement:**
```powershell
cd frontend_irrig
npm start
```

✅ Le frontend s'ouvrira automatiquement sur: `http://localhost:3000`

---

### Étape 3️⃣ : Vérifier la connexion

1. Ouvrir `http://localhost:3000` dans votre navigateur
2. Vérifier l'indicateur en haut du dashboard:
   - 🟢 **"Backend connecté"** → Tout fonctionne !
   - 🔴 **"Backend déconnecté"** → Vérifier que le backend est démarré

---

## 📊 Ce que vous verrez

Le dashboard affiche en temps réel:
- ✅ **État de la pompe** (Active/Inactive)
- ✅ **Humidité moyenne du sol** avec gauge circulaire
- ✅ **3 niveaux d'humidité** (10cm, 30cm, 60cm)
- ✅ **Graphique de consommation d'eau** (30 derniers jours)
- ✅ **6 capteurs**: Température, Humidité Air, Humidité Sol, pH, Luminosité, Vent

Les données se rafraîchissent automatiquement toutes les 5 secondes.

---

## 🔧 Dépannage rapide

### Le backend ne démarre pas
```powershell
# Installer les dépendances
cd backend
pip install -r requirements.txt
```

### Le frontend ne démarre pas
```powershell
# Installer les dépendances
cd frontend_irrig
npm install
```

### "Backend déconnecté" affiché
1. Vérifier que le backend est démarré sur le port 8000
2. Tester: `curl http://localhost:8000/`
3. Vérifier les logs dans le terminal du backend

---

## 🎯 Prochaines actions

Une fois le système démarré, vous pouvez:
- 📈 Consulter les statistiques en temps réel
- 🎮 Contrôler la pompe (à implémenter dans l'UI)
- 📊 Visualiser l'historique des données
- ⚙️ Modifier la configuration

---

## 📞 Endpoints principaux

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/history?limit=1` | GET | Dernières données capteurs |
| `/historique-24h` | GET | Historique 24h |
| `/valve-state/zone_1` | GET | État de la pompe |
| `/toggle-valve` | POST | Contrôler la pompe |
| `/statistiques-eau` | GET | Stats de consommation |

Documentation complète: `http://localhost:8000/docs`

---

**C'est parti ! 🌱💧**
