# 🔧 Guide de Dépannage - Liaison Backend/Frontend

## ⚠️ Problème: "Les anciennes données statiques sont toujours affichées"

### 📋 Checklist de Diagnostic

#### ✅ Étape 1: Vérifier que les services sont démarrés

1. **Backend (Port 8000)**: Dans un terminal
```powershell
cd C:\diengsalaa\Supnum_L3_S5\irraga\smartirrig\backend
uvicorn main:app --reload
```

2. **Simulation (Envoyer des données)**: Dans un autre terminal
```powershell
cd C:\diengsalaa\Supnum_L3_S5\irraga\smartirrig\simulation
python simulation_backend.py
```

3. **Frontend (Port 3000)**: Dans un autre terminal
```powershell
cd C:\diengsalaa\Supnum_L3_S5\irraga\smartirrig\frontend_irrig
npm start
```

---

#### ✅ Étape 2: Tester la connexion backend

**Option A: Utiliser le fichier de test HTML**
1. Ouvrir dans un navigateur: `C:\diengsalaa\Supnum_L3_S5\irraga\smartirrig\test-connexion.html`
2. Cliquer sur "🚀 Tester la Connexion"
3. Vérifier que le statut est ✅ VERT

**Option B: Tester manuellement dans le navigateur**
1. Ouvrir: http://localhost:8000/
   - ✅ Devrait afficher: `{"message":"IoT Irrigation Backend Running"}`
2. Ouvrir: http://localhost:8000/history?limit=1
   - ✅ Devrait afficher des données JSON de capteurs

---

#### ✅ Étape 3: Vérifier le Dashboard React

1. **Ouvrir le Dashboard**: http://localhost:3000

2. **Vérifier l'indicateur de connexion** (en haut de la page):
   - 🟢 **"Backend connecté"** → Tout fonctionne !
   - 🔴 **"Backend déconnecté"** → Problème de connexion

3. **Ouvrir la Console du Navigateur** (F12):
   - Chercher des erreurs en rouge
   - Chercher "Erreur lors de la récupération des données"
   - Chercher des erreurs CORS

---

#### ✅ Étape 4: Forcer le rechargement du Frontend

Le navigateur peut avoir mis en cache l'ancienne version. **Forcer le rechargement**:

1. **Sur le Dashboard (localhost:3000)**:
   - Appuyer sur `Ctrl + Shift + R` (Windows)
   - Ou `Ctrl + F5`
   - Ou vider le cache: F12 → Onglet "Réseau" → Clic droit → "Vider le cache"

2. **Redémarrer le serveur React** (si nécessaire):
```powershell
# Arrêter avec Ctrl+C puis relancer
cd C:\diengsalaa\Supnum_L3_S5\irraga\smartirrig\frontend_irrig
npm start
```

---

### 🔍 Diagnostic Avancé

#### Problème: Backend déconnecté (🔴)

**Causes possibles:**

1. **Le backend n'est pas démarré**
   - Solution: Relancer `uvicorn main:app --reload` dans le dossier backend

2. **Mauvaise URL dans le frontend**
   - Vérifier: `frontend_irrig/src/services/api.js`
   - La ligne devrait être: `const API_BASE_URL = 'http://localhost:8000';`

3. **Problème CORS**
   - Vérifier dans le backend `main.py` que CORS autorise `localhost:3000`
   - Devrait contenir:
   ```python
   allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"]
   ```

4. **Port 8000 déjà utilisé**
   - Vérifier avec: `netstat -ano | findstr :8000`
   - Tuer le processus ou changer de port

---

#### Problème: Données vides ou "null"

**Causes possibles:**

1. **La base de données est vide**
   - Solution: Lancer la simulation pour envoyer des données
   ```powershell
   cd simulation
   python simulation_backend.py
   ```
   - Laisser tourner quelques secondes

2. **MongoDB n'est pas démarré**
   - Vérifier que MongoDB est installé et démarré
   - Ou utiliser MongoDB Atlas (cloud)

---

#### Problème: Données statiques toujours affichées

**Solution 1: Vérifier que le service API est bien importé**

Dans `Dashboard.js`, vérifier la ligne 3:
```javascript
import apiService from '../services/api';
```

**Solution 2: Vérifier que la fonction fetchBackendData est appelée**

Ouvrir la Console du navigateur (F12) et taper:
```javascript
// Devrait afficher les données ou null
console.log('Test API');
fetch('http://localhost:8000/history?limit=1')
  .then(r => r.json())
  .then(d => console.log(d));
```

**Solution 3: Supprimer node_modules et réinstaller**
```powershell
cd frontend_irrig
Remove-Item -Recurse -Force node_modules
Remove-Item -Force package-lock.json
npm install
npm start
```

---

### 📝 Checklist Finale

Avant de dire que ça ne fonctionne pas, vérifier:

- [ ] ✅ Backend démarré et accessible sur http://localhost:8000/
- [ ] ✅ Simulation envoyant des données (optionnel mais recommandé)
- [ ] ✅ Frontend démarré sur http://localhost:3000
- [ ] ✅ Indicateur de connexion VERT sur le dashboard
- [ ] ✅ Console du navigateur sans erreurs (F12)
- [ ] ✅ Cache du navigateur vidé (Ctrl+Shift+R)
- [ ] ✅ Les valeurs des capteurs changent toutes les 5 secondes

---

### 🎯 Test Rapide Final

**Commande PowerShell pour tout tester d'un coup:**

```powershell
# Tester si backend répond
Invoke-RestMethod -Uri "http://localhost:8000/" -Method Get

# Tester les données
Invoke-RestMethod -Uri "http://localhost:8000/history?limit=1" -Method Get
```

Si ces commandes retournent des données JSON, le backend fonctionne correctement !

---

### 📞 Aide Supplémentaire

Si le problème persiste après avoir suivi tous ces steps:

1. **Copier les erreurs** de la console (F12)
2. **Copier les logs** du terminal backend
3. **Faire une capture d'écran** du dashboard
4. **Vérifier** le fichier `test-connexion.html` (devrait être VERT)

Le problème peut alors être identifié précisément !
