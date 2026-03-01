# 🌱 Smart Irrigation System - Guide d'Intégration Backend/Frontend

## 📋 Vue d'ensemble

Ce projet connecte un backend FastAPI (Python) avec un frontend React pour créer un système d'irrigation intelligent avec monitoring en temps réel.

## 🏗️ Architecture

```
smartirrig/
├── backend/                 # API FastAPI (Python)
│   ├── main.py             # Serveur principal avec endpoints
│   ├── database.py         # Configuration MongoDB
│   ├── models.py           # Modèles de données
│   ├── irrigation_logic.py # Logique d'irrigation intelligente
│   └── requirements.txt    # Dépendances Python
│
└── frontend_irrig/         # Application React
    ├── src/
    │   ├── components/
    │   │   └── Dashboard.js      # Dashboard principal
    │   └── services/
    │       └── api.js            # Service API pour backend
    └── package.json
```

## 🚀 Démarrage - Backend

### 1. Prérequis
- Python 3.8+
- MongoDB (local ou Atlas)
- pip

### 2. Installation des dépendances

```bash
cd smartirrig/backend
pip install -r requirements.txt
```

### 3. Démarrer le serveur backend

```bash
# Démarrer FastAPI sur le port 8000
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Le backend sera accessible à:** `http://localhost:8000`

### 4. Vérifier que le backend fonctionne

Ouvrir dans le navigateur:
- Documentation API: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/`

## 🎨 Démarrage - Frontend

### 1. Prérequis
- Node.js 14+
- npm ou yarn

### 2. Installation des dépendances

```bash
cd smartirrig/frontend_irrig
npm install
```

### 3. Démarrer l'application React

```bash
npm start
```

**Le frontend sera accessible à:** `http://localhost:3000`

## 🔗 Connexion Backend/Frontend

### Configuration de l'API

Le frontend est configuré pour se connecter au backend via le fichier:
```
frontend_irrig/src/services/api.js
```

**URL par défaut:** `http://localhost:8000`

Pour modifier l'URL du backend, éditer cette ligne dans `api.js`:
```javascript
const API_BASE_URL = 'http://localhost:8000';
```

### Vérification de la connexion

1. **Démarrer le backend** (port 8000)
2. **Démarrer le frontend** (port 3000)
3. **Ouvrir** `http://localhost:3000`
4. **Vérifier l'indicateur** en haut du dashboard:
   - 🟢 "Backend connecté" → Connexion réussie
   - 🔴 "Backend déconnecté" → Vérifier que le backend est démarré

## 📡 Endpoints API Disponibles

### Données en temps réel
- `GET /history?limit=1` - Dernières données des capteurs
- `GET /historique-24h` - Historique des 24 dernières heures
- `GET /valve-state/{zone_id}` - État de la valve d'irrigation

### Contrôle
- `POST /toggle-valve` - Activer/désactiver la pompe
- `POST /configuration` - Modifier la configuration
- `POST /set-weather` - Définir la météo

### Statistiques
- `GET /statistiques-eau` - Consommation d'eau
- `GET /reservoir-eau` - Niveau du réservoir
- `GET /alertes-logs` - Alertes et événements

### Documentation complète
Accéder à `http://localhost:8000/docs` pour voir tous les endpoints disponibles.

## 🔄 Flux de données

```
Capteurs → Backend (MongoDB) → API REST → Frontend React → Dashboard
           ↓                                    ↑
      Logique d'irrigation              Rafraîchissement 5s
```

1. **Backend** reçoit les données des capteurs (réels ou simulés)
2. **Logique d'irrigation** décide si irrigation nécessaire
3. **MongoDB** stocke l'historique
4. **Frontend** récupère les données toutes les 5 secondes
5. **Dashboard** affiche les données en temps réel

## 📊 Fonctionnalités principales

### Backend
- ✅ Décision d'irrigation intelligente multi-facteurs
- ✅ Gestion de réservoir d'eau
- ✅ Système d'alertes
- ✅ Statistiques de consommation
- ✅ Prédiction d'humidité (ML)
- ✅ API RESTful avec CORS

### Frontend
- ✅ Dashboard moderne et responsive
- ✅ Affichage temps réel des capteurs
- ✅ Graphique de consommation d'eau
- ✅ Indicateur d'état de la pompe
- ✅ Niveaux d'humidité du sol (3 profondeurs)
- ✅ Indicateur de connexion backend

## 🛠️ Débogage

### Le frontend ne se connecte pas au backend

1. **Vérifier que le backend est démarré**
   ```bash
   curl http://localhost:8000/
   # Devrait retourner: {"message":"IoT Irrigation Backend Running"}
   ```

2. **Vérifier les logs du backend**
   - Les requêtes apparaissent dans le terminal du backend

3. **Vérifier CORS**
   - Le backend accepte les requêtes de `localhost:3000` et `localhost:3001`

4. **Vérifier la console du navigateur (F12)**
   - Rechercher les erreurs réseau

### Problème de données

1. **Aucune donnée affichée**
   - Vérifier que MongoDB est démarré
   - Envoyer des données test via `/send-manual-data`

2. **Données anciennes**
   - Le frontend rafraîchit toutes les 5 secondes
   - Vérifier que le backend reçoit de nouvelles données

## 📝 Commandes utiles

### Backend
```bash
# Démarrer
uvicorn main:app --reload

# Vérifier les logs
# Les logs apparaissent dans le terminal

# Tester un endpoint
curl http://localhost:8000/history?limit=5
```

### Frontend
```bash
# Démarrer en mode développement
npm start

# Build pour production
npm run build

# Installer une nouvelle dépendance
npm install <package-name>
```

## 🎯 Prochaines étapes

1. ✅ Intégration backend/frontend réussie
2. 🔄 Ajouter les graphiques historiques avancés
3. 🔄 Implémenter la gestion des alertes en temps réel
4. 🔄 Ajouter l'authentification utilisateur
5. 🔄 Créer une page de configuration interactive
6. 🔄 Ajouter des notifications push

## 📞 Support

En cas de problème:
1. Vérifier les logs du backend et du frontend
2. Consulter la documentation API: `http://localhost:8000/docs`
3. Vérifier que tous les services sont démarrés (Backend, MongoDB)

## 🎉 Félicitations !

Votre système d'irrigation intelligent est maintenant connecté et fonctionnel ! 🌿💧
