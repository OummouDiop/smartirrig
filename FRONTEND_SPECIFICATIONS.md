# 📱 SmartIrrig - Spécifications Frontend

## 📋 Table des matières
- [Vue d'ensemble](#vue-densemble)
- [Architecture du système](#architecture-du-système)
- [API Backend - Endpoints](#api-backend---endpoints)
- [Modèles de données](#modèles-de-données)
- [Fonctionnalités à implémenter](#fonctionnalités-à-implémenter)
- [Recommandations techniques](#recommandations-techniques)
- [Exemples de code](#exemples-de-code)

---

## 🎯 Vue d'ensemble

**SmartIrrig** est un système d'irrigation intelligente IoT qui utilise des capteurs pour optimiser l'arrosage des cultures en temps réel.

### Objectifs du système
- 💧 **Économie d'eau** : Réduction de 30-50% de la consommation
- 🌱 **Optimisation** : Irrigation basée sur les besoins réels de la plante
- 📊 **Monitoring** : Suivi en temps réel de tous les paramètres
- 🤖 **Intelligence** : Décisions automatiques basées sur ML

### Technologies Backend
- **Framework** : FastAPI (Python)
- **Base de données** : MongoDB
- **Machine Learning** : scikit-learn (prédiction d'humidité)
- **API** : RESTful avec CORS activé
- **Port** : 8000 (http://127.0.0.1:8000)

---

## 🏗️ Architecture du système

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (React/Vue/Angular)          │
│  - Dashboard temps réel                                  │
│  - Graphiques & Analytics                                │
│  - Configuration dynamique                               │
│  - Contrôle manuel des vannes                            │
└────────────────┬────────────────────────────────────────┘
                 │ HTTP/REST API
                 │ WebSocket (à implémenter)
┌────────────────▼────────────────────────────────────────┐
│              BACKEND FastAPI (Port 8000)                 │
│  - Logic d'irrigation intelligente                       │
│  - Algorithmes ML (prédiction)                           │
│  - Gestion des alertes                                   │
│  - Statistiques & Analytics                              │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│                    MongoDB Database                      │
│  - sensor_data (données capteurs)                        │
│  - valve_states (états des vannes)                       │
└─────────────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│              SIMULATION Python Scripts                   │
│  - simulation_backend.py (auto, toutes les 5s)          │
│  - simulation_manuelle.py (tests manuels)               │
└─────────────────────────────────────────────────────────┘
```

---

## 🔌 API Backend - Endpoints

### Base URL
```
http://127.0.0.1:8000
```

### 1️⃣ **Endpoints principaux**

#### `GET /`
Vérification que le backend est actif
```json
Response: {
  "message": "IoT Irrigation Backend Running"
}
```

---

### 2️⃣ **Données capteurs**

#### `POST /send-data`
Envoi automatique des données capteurs (utilisé par la simulation)
```json
Request Body: {
  "zone_id": "zone-1",
  "humidity": 60.5,              // Humidité de l'air (%)
  "temperature": 25.3,           // Température (°C)
  "soil_moisture": 45.2,         // Humidité sol moyenne (%)
  "soil_moisture_10cm": 40.0,    // Humidité 10cm profondeur (%)
  "soil_moisture_30cm": 45.0,    // Humidité 30cm profondeur (%)
  "soil_moisture_60cm": 50.0,    // Humidité 60cm profondeur (%)
  "soil_ph": 6.5,                // pH du sol
  "light": 450.0,                // Luminosité (lux)
  "wind_speed": 8.0,             // Vitesse du vent (km/h)
  "rainfall": false,             // Pluie détectée (boolean)
  "rainfall_intensity": "none",  // "light", "moderate", "heavy", "none"
  "pump_was_active": false       // État précédent de la pompe
}

Response: {
  "pump": true,                  // Décision: activer la pompe?
  "message": "🚿 Irrigation ACTIVÉE - Sol sec (45.2%)"
}
```

#### `POST /send-manual-data`
Envoi manuel de données pour tests (même structure que `/send-data`)
- Déclenche une synchronisation avec la simulation automatique
- Marque les données comme `source: "manual"`

#### `GET /simulation-status`
Récupère l'état de synchronisation avec la simulation
```json
Response: {
  "manual_data_received": false,
  "latest_data": {
    "soil_moisture_10cm": 45,
    "soil_moisture_30cm": 55,
    "soil_moisture_60cm": 65,
    "temperature": 25,
    "humidity": 60,
    "pump_active": false
  }
}
```

---

### 3️⃣ **Historique des données**

#### `GET /history?zone_id=zone-1`
Récupère les 100 dernières données capteurs
```json
Response: [
  {
    "id": "507f1f77bcf86cd799439011",
    "zone_id": "zone-1",
    "timestamp": 1709049600000,      // milliseconds
    "moisture": 45.2,
    "temperature": 25.3,
    "humidity": 60.5,
    "soilMoisture10cm": 40.0,
    "soilMoisture30cm": 45.0,
    "soilMoisture60cm": 50.0,
    "light": 450.0,
    "windSpeed": 8.0,
    "rainfall": false,
    "rainfallIntensity": "none",
    "created_at": "2024-02-27T14:30:00"
  }
]
```

#### `GET /historique-24h`
Historique optimisé des 24 dernières heures (max 288 points)
```json
Response: {
  "data": [...],
  "total_points": 250,
  "periode": "24 heures"
}
```

---

### 4️⃣ **Contrôle des vannes**

#### `POST /toggle-valve`
Contrôle manuel d'une vanne d'irrigation
```json
Request Body: {
  "zone_id": "zone-1",
  "valve_open": true              // true = ouvrir, false = fermer
}

Response: {
  "zone_id": "zone-1",
  "valve_open": true,
  "message": "IRRIGATION ACTIVEE - Vanne ouverte pour zone-1"
}
```

#### `GET /valve-state/{zone_id}`
Récupère l'état actuel d'une vanne
```json
Response: {
  "zone_id": "zone-1",
  "valve_open": false,
  "updated_at": "2024-02-27T14:30:00"
}
```

---

### 5️⃣ **Météo (simulation)**

#### `POST /set-weather?condition={sunny|cloudy|rainy|auto}`
Force les conditions météo pour les tests
```json
Response: {
  "message": "☀️ Temps forcé : Ensoleillé",
  "condition": "sunny"
}
```

#### `GET /get-weather`
Récupère les conditions météo forcées
```json
Response: {
  "condition": "sunny",           // null si mode auto
  "rain_intensity": null
}
```

---

### 6️⃣ **Configuration dynamique**

#### `GET /configuration`
Récupère la configuration actuelle
```json
Response: {
  "type_plante": "tomates",
  "saison": "ete",                // printemps, ete, automne, hiver
  "mode": "eco",                  // eco ou intensif
  "seuil_declenchement": 50,      // % humidité pour démarrer irrigation
  "seuil_arret": 80               // % humidité pour arrêter irrigation
}
```

#### `POST /configuration`
Met à jour la configuration SANS redémarrage
```json
Request Body: {
  "type_plante": "tomates",
  "saison": "ete",
  "mode": "eco",
  "seuil_declenchement": 45,
  "seuil_arret": 75
}

Response: {
  "success": true,
  "message": "Configuration mise à jour sans redémarrage",
  "config": { ... }
}
```

---

### 7️⃣ **Alertes & Logs**

#### `GET /alertes-logs?limit=20`
Récupère les événements et alertes récents
```json
Response: {
  "logs": [
    {
      "timestamp": 1709049600000,
      "time": "14:30",
      "message": "14:30 - Début arrosage (Cause: Sécheresse)",
      "type": "irrigation_start",    // irrigation_start, irrigation_stop, alert_wind, etc.
      "zone_id": "zone-1"
    }
  ],
  "total": 45
}
```

#### `DELETE /alertes-logs`
Efface tous les logs (utile pour les tests)

---

### 8️⃣ **Statistiques d'eau**

#### `GET /statistiques-eau`
Statistiques de consommation et économies
```json
Response: {
  "eau_intelligente": 125.5,           // Litres utilisés (système intelligent)
  "eau_traditionnelle": 245.8,         // Litres qu'on aurait utilisé (traditionnel)
  "economie_litres": 120.3,            // Économie en litres
  "economie_pourcentage": 48.9,        // % d'économie
  "temps_irrigation_intelligent_minutes": 12.5,
  "temps_irrigation_traditionnel_minutes": 24.6,
  "temps_economise_minutes": 12.1,
  "cycles_evites_pluie": 3,            // Cycles évités grâce à la pluie
  "date_debut": "2024-02-27T10:00:00"
}
```

#### `POST /statistiques-eau/reset`
Réinitialise les statistiques

---

### 9️⃣ **Réservoir d'eau**

#### `GET /reservoir-eau`
État du réservoir d'eau
```json
Response: {
  "capacite_totale": 1000.0,          // Litres
  "niveau_actuel": 200.0,             // Litres
  "pourcentage": 20.0,                // %
  "statut": "bas",                    // critique, bas, moyen, bon
  "message": "⚠️ Niveau bas - Remplissage recommandé",
  "irrigation_bloquee": false,
  "seuils": {
    "critique": 10.0,
    "bas": 25.0,
    "moyen": 50.0
  }
}
```

#### `POST /reservoir-eau/remplir?litres=500`
Remplit le réservoir (sans paramètre = remplissage complet)
```json
Response: {
  "message": "Ajout de 500L au réservoir",
  "niveau_actuel": 700.0,
  "pourcentage": 70.0
}
```

---

### 🔟 **Machine Learning - Prédiction**

#### `GET /predict-soil-moisture/{zone_id}`
Prédiction de l'humidité du sol (basée sur les 5 derniers points)
```json
Response: {
  "prediction": 42.5,               // Humidité prédite (%)
  "error": null,
  "confidence": 85.3,               // Confiance du modèle (%)
  "num_samples_used": 5
}
```

---

### 1️⃣1️⃣ **Dashboard - Endpoints consolidés**

#### `GET /dashboard/moisture-metrics`
Métriques d'humidité par zone
```json
Response: {
  "totalMoisture": 55.2,
  "averageMoisture": 55.2,
  "totalLand": 66.7,                 // % de zones actives
  "zones": [
    {
      "zone_id": "zone-1",
      "moisture": 55.2
    }
  ]
}
```

#### `GET /dashboard/alarm-history`
Historique des alarmes (7 derniers jours)
```json
Response: {
  "data": [
    {
      "day": "Monday",
      "alarms": 3,
      "date": "2024-02-26"
    }
  ],
  "totalAlarms": 12
}
```

#### `GET /dashboard/ph-history`
Historique du pH (24 dernières heures)
```json
Response: {
  "data": [
    {
      "timestamp": 1709049600000,
      "time": "14:30",
      "ph": 6.5,
      "zone_id": "zone-1"
    }
  ],
  "currentPh": 6.5,
  "minPh": 6.2,
  "maxPh": 6.8,
  "avgPh": 6.5
}
```

#### `GET /dashboard/water-usage`
Utilisation d'eau par jour (7 derniers jours)
```json
Response: {
  "data": [
    {
      "day": "Mon",
      "date": "2024-02-26",
      "usage": 125.5,
      "unit": "L"
    }
  ],
  "totalUsage": 875.5,
  "averageDaily": 125.1,
  "unit": "Litres"
}
```

#### `GET /dashboard/summary`
**🔥 ENDPOINT OPTIMISÉ - Toutes les données dashboard en 1 appel**
```json
Response: {
  "moisture": { ... },               // Données de moisture-metrics
  "alarms": { ... },                 // Données de alarm-history
  "ph": { ... },                     // Données de ph-history
  "waterUsage": { ... }              // Données de water-usage
}
```

---

## 📊 Modèles de données

### SensorData
```typescript
interface SensorData {
  zone_id: string;
  humidity: number;              // 0-100%
  temperature: number;           // °C
  soil_moisture: number;         // 0-100%
  soil_moisture_10cm?: number;   // 0-100%
  soil_moisture_30cm?: number;   // 0-100%
  soil_moisture_60cm?: number;   // 0-100%
  soil_ph?: number;              // 0-14
  light?: number;                // lux
  wind_speed?: number;           // km/h
  rainfall: boolean;
  rainfall_intensity: 'light' | 'moderate' | 'heavy' | 'none';
  pump_was_active: boolean;
}
```

### IrrigationDecision
```typescript
interface IrrigationDecision {
  pump: boolean;                 // true = activer irrigation
  message: string;               // Message explicatif
}
```

### Configuration
```typescript
interface Configuration {
  type_plante: string;           // "tomates", "carottes", etc.
  saison: 'printemps' | 'ete' | 'automne' | 'hiver';
  mode: 'eco' | 'intensif';
  seuil_declenchement: number;   // 0-100%
  seuil_arret: number;           // 0-100%
}
```

### AlertLog
```typescript
interface AlertLog {
  timestamp: number;             // milliseconds
  time: string;                  // "HH:MM"
  message: string;
  type: 'irrigation_start' | 'irrigation_stop' | 'alert_wind' | 
        'alert_reservoir_bas' | 'alert_reservoir_critique' | 'config_change';
  zone_id: string;
}
```

---

## 🎨 Fonctionnalités à implémenter

### 1. **Dashboard principal** 🏠

#### Widgets en temps réel
- 🌡️ **Température actuelle** avec graphique 24h
- 💧 **Humidité du sol** (3 profondeurs) avec jauges visuelles
- 💦 **Humidité de l'air** avec tendance
- 🧪 **pH du sol** avec indicateur de santé
- ☀️ **Luminosité** (jour/nuit)
- 🌬️ **Vitesse du vent** avec alertes
- 🌧️ **Pluie** (oui/non + intensité)
- 🚿 **État de la pompe** (ON/OFF) avec indicateur visuel

#### Métriques globales
- 📊 Total Moisture (%)
- 📈 Average Moisture (%)
- 🌍 Total Land (% zones actives)

#### Graphiques
- 📉 **Courbe d'humidité** (24h) - multi-profondeur
- 📊 **Historique d'arrosage** (durée, fréquence)
- 🧪 **Évolution du pH** (24h)
- 💧 **Consommation d'eau** (7 derniers jours)
- ⚠️ **Alarmes** (7 derniers jours)

---

### 2. **Page Statistiques** 📊

#### Économies d'eau
- 💧 Eau économisée (litres + %)
- 📉 Graphique comparatif intelligent vs traditionnel
- ⏱️ Temps d'irrigation économisé
- 🌧️ Cycles évités grâce à la pluie

#### Performance du système
- ✅ Taux de disponibilité
- 🎯 Précision des décisions
- 📈 Tendances sur 7/30 jours

---

### 3. **Page Configuration** ⚙️

#### Paramètres culture
- 🌱 Type de plante (dropdown)
- 🍂 Saison (printemps, été, automne, hiver)
- ⚡ Mode (éco / intensif)

#### Seuils d'irrigation
- 📉 Seuil de déclenchement (slider 0-100%)
- 📈 Seuil d'arrêt (slider 0-100%)
- 👁️ Prévisualisation en temps réel

#### Sauvegarde
- ✅ Bouton "Appliquer" (pas de redémarrage nécessaire)
- 🔄 Bouton "Réinitialiser aux valeurs par défaut"

---

### 4. **Page Contrôle Manuel** 🎮

#### Contrôles directs
- 🚿 **Toggle irrigation** par zone
  - Gros bouton ON/OFF avec confirmation
  - État actuel visible
  - Durée écoulée depuis activation

#### Tests météo
- ☀️ Forcer ensoleillé
- ☁️ Forcer nuageux
- 🌧️ Forcer pluie
- 🔄 Mode automatique

---

### 5. **Page Réservoir** 🚰

#### Visualisation
- 📊 Jauge visuelle du niveau (0-100%)
- 💧 Niveau actuel (litres)
- 📈 Capacité totale
- ⚠️ Alertes (critique, bas, moyen, bon)

#### Actions
- ➕ Remplir (quantité personnalisée)
- 🔄 Remplissage complet
- 📜 Historique de remplissage

#### Statistiques
- 💦 Consommation journalière moyenne
- 📅 Prochaine date de remplissage estimée

---

### 6. **Page Alertes & Logs** ⚠️

#### Filtres
- 🔍 Par type d'événement
- 📅 Par date
- 🌍 Par zone

#### Liste des événements
- ⏰ Timestamp
- 📝 Message descriptif
- 🏷️ Type coloré (badge)
- 🌍 Zone concernée

#### Actions
- 🗑️ Effacer les logs
- 📥 Exporter en CSV/JSON

---

### 7. **Page Prédictions** 🔮

#### ML Insights
- 📈 Prédiction d'humidité (prochaines heures)
- 🎯 Confiance du modèle (%)
- 📊 Graphique tendance vs prédiction
- 💡 Recommandations automatiques

---

### 8. **Fonctionnalités transversales** 🌐

#### Navigation
- 🧭 Sidebar ou Navbar avec icônes
- 📱 Responsive (mobile, tablet, desktop)
- 🎨 Dark mode / Light mode

#### Notifications
- 🔔 Toast notifications pour événements
- ⚠️ Alertes critiques (réservoir vide, etc.)
- ✅ Confirmations d'actions

#### Temps réel
- 🔄 Auto-refresh toutes les 5 secondes (dashboard)
- 📡 WebSocket (optionnel, à implémenter côté backend)
- 🟢 Indicateur de connexion backend

#### Exportation
- 📥 Exporter données en CSV
- 📊 Générer rapports PDF
- 📧 Envoi par email (optionnel)

---

## 💡 Recommandations techniques

### Stack Frontend suggéré
```
Option 1 (React):
- React 18+ avec TypeScript
- Vite (build tool)
- TailwindCSS ou Material-UI
- Chart.js ou Recharts (graphiques)
- Axios ou React Query (API calls)
- React Router (navigation)
- Zustand ou Redux (state management)

Option 2 (Vue):
- Vue 3 avec TypeScript
- Vite
- Vuetify ou PrimeVue
- Chart.js ou Apache ECharts
- Axios
- Vue Router
- Pinia (state management)

Option 3 (Angular):
- Angular 17+
- Angular Material
- ngx-charts
- HttpClient
- Angular Router
```

### Architecture Frontend
```
src/
├── components/
│   ├── dashboard/
│   │   ├── MetricCard.tsx
│   │   ├── SensorWidget.tsx
│   │   ├── ChartCard.tsx
│   │   └── AlertBanner.tsx
│   ├── common/
│   │   ├── Navbar.tsx
│   │   ├── Sidebar.tsx
│   │   └── LoadingSpinner.tsx
│   └── controls/
│       ├── ValveToggle.tsx
│       ├── WeatherControl.tsx
│       └── ConfigForm.tsx
├── pages/
│   ├── Dashboard.tsx
│   ├── Statistics.tsx
│   ├── Configuration.tsx
│   ├── ManualControl.tsx
│   ├── Reservoir.tsx
│   ├── Alerts.tsx
│   └── Predictions.tsx
├── services/
│   ├── api.ts              // Service API principal
│   ├── websocket.ts        // WebSocket (futur)
│   └── utils.ts
├── types/
│   └── api.types.ts        // Types TypeScript
├── stores/
│   └── appStore.ts         // State management
└── App.tsx
```

### Gestion d'état suggérée
```typescript
// Exemple avec Zustand (React)
interface AppState {
  // Données capteurs
  currentSensorData: SensorData | null;
  sensorHistory: SensorData[];
  
  // Configuration
  configuration: Configuration;
  
  // États UI
  isConnected: boolean;
  lastUpdate: Date;
  
  // Actions
  fetchSensorData: () => Promise<void>;
  updateConfiguration: (config: Configuration) => Promise<void>;
  toggleValve: (zoneId: string, open: boolean) => Promise<void>;
}
```

### Polling vs WebSocket
```typescript
// Option 1: Polling (simple, déjà utilisable)
useEffect(() => {
  const interval = setInterval(() => {
    fetchSensorData();
  }, 5000); // Toutes les 5 secondes
  
  return () => clearInterval(interval);
}, []);

// Option 2: WebSocket (à implémenter côté backend)
// Plus efficace pour temps réel
const ws = new WebSocket('ws://127.0.0.1:8000/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  updateSensorData(data);
};
```

---

## 🔧 Exemples de code

### 1. Service API (TypeScript)

```typescript
// services/api.ts
import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Intercepteur pour gérer les erreurs globalement
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    // Gérer les erreurs réseau
    if (!error.response) {
      throw new Error('Backend non accessible. Vérifiez que le serveur est démarré.');
    }
    throw error;
  }
);

export class SmartIrrigAPI {
  // GET - Historique des données
  static async getHistory(zoneId?: string): Promise<SensorData[]> {
    const params = zoneId ? { zone_id: zoneId } : {};
    const response = await api.get('/history', { params });
    return response.data;
  }

  // GET - Historique 24h
  static async getHistorique24h() {
    const response = await api.get('/historique-24h');
    return response.data;
  }

  // GET - Configuration
  static async getConfiguration(): Promise<Configuration> {
    const response = await api.get('/configuration');
    return response.data;
  }

  // POST - Mettre à jour configuration
  static async updateConfiguration(config: Configuration) {
    const response = await api.post('/configuration', config);
    return response.data;
  }

  // POST - Toggle valve
  static async toggleValve(zoneId: string, valveOpen: boolean) {
    const response = await api.post('/toggle-valve', {
      zone_id: zoneId,
      valve_open: valveOpen,
    });
    return response.data;
  }

  // GET - État valve
  static async getValveState(zoneId: string) {
    const response = await api.get(`/valve-state/${zoneId}`);
    return response.data;
  }

  // POST - Forcer météo
  static async setWeather(condition: 'sunny' | 'cloudy' | 'rainy' | 'auto') {
    const response = await api.post(`/set-weather?condition=${condition}`);
    return response.data;
  }

  // GET - Alertes et logs
  static async getAlertes(limit = 20) {
    const response = await api.get(`/alertes-logs?limit=${limit}`);
    return response.data;
  }

  // GET - Statistiques eau
  static async getStatistiquesEau() {
    const response = await api.get('/statistiques-eau');
    return response.data;
  }

  // GET - Réservoir
  static async getReservoir() {
    const response = await api.get('/reservoir-eau');
    return response.data;
  }

  // POST - Remplir réservoir
  static async remplirReservoir(litres?: number) {
    const url = litres 
      ? `/reservoir-eau/remplir?litres=${litres}` 
      : '/reservoir-eau/remplir';
    const response = await api.post(url);
    return response.data;
  }

  // GET - Prédiction ML
  static async predictSoilMoisture(zoneId: string) {
    const response = await api.get(`/predict-soil-moisture/${zoneId}`);
    return response.data;
  }

  // GET - Dashboard summary (OPTIMISÉ)
  static async getDashboardSummary() {
    const response = await api.get('/dashboard/summary');
    return response.data;
  }

  // GET - Métriques d'humidité
  static async getMoistureMetrics() {
    const response = await api.get('/dashboard/moisture-metrics');
    return response.data;
  }

  // GET - Historique alarmes
  static async getAlarmHistory() {
    const response = await api.get('/dashboard/alarm-history');
    return response.data;
  }

  // GET - Historique pH
  static async getPhHistory() {
    const response = await api.get('/dashboard/ph-history');
    return response.data;
  }

  // GET - Consommation d'eau
  static async getWaterUsage() {
    const response = await api.get('/dashboard/water-usage');
    return response.data;
  }
}

export default SmartIrrigAPI;
```

---

### 2. Composant Dashboard (React)

```tsx
// pages/Dashboard.tsx
import React, { useEffect, useState } from 'react';
import { SmartIrrigAPI } from '../services/api';
import MetricCard from '../components/dashboard/MetricCard';
import ChartCard from '../components/dashboard/ChartCard';
import { Line } from 'react-chartjs-2';

const Dashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [isConnected, setIsConnected] = useState(true);

  // Fetch dashboard data
  const fetchDashboard = async () => {
    try {
      const data = await SmartIrrigAPI.getDashboardSummary();
      setDashboardData(data);
      setIsConnected(true);
    } catch (error) {
      console.error('Erreur chargement dashboard:', error);
      setIsConnected(false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();

    // Auto-refresh toutes les 5 secondes
    const interval = setInterval(fetchDashboard, 5000);

    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <LoadingSpinner />;
  }

  if (!isConnected) {
    return (
      <div className="alert alert-danger">
        ❌ Backend non accessible. Vérifiez que le serveur est démarré.
      </div>
    );
  }

  const { moisture, ph, alarms, waterUsage } = dashboardData;

  return (
    <div className="dashboard">
      {/* Indicateur de connexion */}
      <div className="connection-status">
        🟢 Connecté - Dernière mise à jour: {new Date().toLocaleTimeString()}
      </div>

      {/* Métriques principales */}
      <div className="metrics-grid">
        <MetricCard
          title="Total Moisture"
          value={`${moisture.totalMoisture}%`}
          icon="💧"
          trend={moisture.totalMoisture > 50 ? 'up' : 'down'}
        />
        <MetricCard
          title="Average Moisture"
          value={`${moisture.averageMoisture}%`}
          icon="📊"
        />
        <MetricCard
          title="Total Land"
          value={`${moisture.totalLand}%`}
          icon="🌍"
        />
        <MetricCard
          title="pH du sol"
          value={ph.currentPh}
          icon="🧪"
          subtext={`Min: ${ph.minPh} / Max: ${ph.maxPh}`}
        />
      </div>

      {/* Graphiques */}
      <div className="charts-grid">
        <ChartCard title="Humidité du sol (24h)">
          <Line
            data={{
              labels: moisture.zones.map((z: any) => z.zone_id),
              datasets: [{
                label: 'Humidité (%)',
                data: moisture.zones.map((z: any) => z.moisture),
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1,
              }],
            }}
          />
        </ChartCard>

        <ChartCard title="Historique pH">
          <Line
            data={{
              labels: ph.data.map((p: any) => p.time),
              datasets: [{
                label: 'pH',
                data: ph.data.map((p: any) => p.ph),
                borderColor: 'rgb(255, 159, 64)',
                tension: 0.1,
              }],
            }}
          />
        </ChartCard>

        <ChartCard title="Consommation d'eau (7 jours)">
          <Bar
            data={{
              labels: waterUsage.data.map((d: any) => d.day),
              datasets: [{
                label: 'Litres',
                data: waterUsage.data.map((d: any) => d.usage),
                backgroundColor: 'rgba(54, 162, 235, 0.5)',
              }],
            }}
          />
        </ChartCard>

        <ChartCard title="Alarmes (7 jours)">
          <Line
            data={{
              labels: alarms.data.map((a: any) => a.day),
              datasets: [{
                label: 'Nombre',
                data: alarms.data.map((a: any) => a.alarms),
                borderColor: 'rgb(255, 99, 132)',
                tension: 0.1,
              }],
            }}
          />
        </ChartCard>
      </div>
    </div>
  );
};

export default Dashboard;
```

---

### 3. Composant Contrôle Manuel (React)

```tsx
// pages/ManualControl.tsx
import React, { useState, useEffect } from 'react';
import { SmartIrrigAPI } from '../services/api';

const ManualControl: React.FC = () => {
  const [valveState, setValveState] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchValveState();
  }, []);

  const fetchValveState = async () => {
    try {
      const state = await SmartIrrigAPI.getValveState('zone-1');
      setValveState(state.valve_open);
    } catch (error) {
      console.error(error);
    }
  };

  const handleToggle = async () => {
    if (loading) return;

    const confirmed = window.confirm(
      `Êtes-vous sûr de vouloir ${valveState ? 'ARRÊTER' : 'DÉMARRER'} l'irrigation ?`
    );

    if (!confirmed) return;

    setLoading(true);
    try {
      await SmartIrrigAPI.toggleValve('zone-1', !valveState);
      setValveState(!valveState);
      // Notification toast
      alert(`Irrigation ${!valveState ? 'ACTIVÉE' : 'ARRÊTÉE'}`);
    } catch (error) {
      console.error(error);
      alert('Erreur lors du contrôle de la vanne');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="manual-control">
      <h1>🎮 Contrôle Manuel</h1>

      <div className="valve-control">
        <h2>Irrigation Zone-1</h2>
        <div className={`status-indicator ${valveState ? 'active' : 'inactive'}`}>
          {valveState ? '🟢 ACTIVE' : '🔴 INACTIVE'}
        </div>

        <button
          className={`toggle-btn ${valveState ? 'btn-danger' : 'btn-success'}`}
          onClick={handleToggle}
          disabled={loading}
        >
          {loading ? 'Chargement...' : (valveState ? '❌ ARRÊTER' : '✅ DÉMARRER')}
        </button>
      </div>

      {/* Contrôle météo */}
      <div className="weather-control">
        <h2>☁️ Forcer les conditions météo</h2>
        <div className="btn-group">
          <button onClick={() => SmartIrrigAPI.setWeather('sunny')}>
            ☀️ Ensoleillé
          </button>
          <button onClick={() => SmartIrrigAPI.setWeather('cloudy')}>
            ☁️ Nuageux
          </button>
          <button onClick={() => SmartIrrigAPI.setWeather('rainy')}>
            🌧️ Pluvieux
          </button>
          <button onClick={() => SmartIrrigAPI.setWeather('auto')}>
            🔄 Automatique
          </button>
        </div>
      </div>
    </div>
  );
};

export default ManualControl;
```

---

### 4. Types TypeScript

```typescript
// types/api.types.ts

export interface SensorData {
  zone_id: string;
  humidity: number;
  temperature: number;
  soil_moisture: number;
  soil_moisture_10cm?: number;
  soil_moisture_30cm?: number;
  soil_moisture_60cm?: number;
  soil_ph?: number;
  light?: number;
  wind_speed?: number;
  rainfall: boolean;
  rainfall_intensity: 'light' | 'moderate' | 'heavy' | 'none';
  pump_was_active: boolean;
}

export interface IrrigationDecision {
  pump: boolean;
  message: string;
}

export interface Configuration {
  type_plante: string;
  saison: 'printemps' | 'ete' | 'automne' | 'hiver';
  mode: 'eco' | 'intensif';
  seuil_declenchement: number;
  seuil_arret: number;
}

export interface AlertLog {
  timestamp: number;
  time: string;
  message: string;
  type: 'irrigation_start' | 'irrigation_stop' | 'alert_wind' | 
        'alert_reservoir_bas' | 'alert_reservoir_critique' | 'config_change';
  zone_id: string;
}

export interface StatistiquesEau {
  eau_intelligente: number;
  eau_traditionnelle: number;
  economie_litres: number;
  economie_pourcentage: number;
  temps_irrigation_intelligent_minutes: number;
  temps_irrigation_traditionnel_minutes: number;
  temps_economise_minutes: number;
  cycles_evites_pluie: number;
  date_debut: string;
}

export interface ReservoirEau {
  capacite_totale: number;
  niveau_actuel: number;
  pourcentage: number;
  statut: 'critique' | 'bas' | 'moyen' | 'bon';
  message: string;
  irrigation_bloquee: boolean;
  seuils: {
    critique: number;
    bas: number;
    moyen: number;
  };
}

export interface MoistureMetrics {
  totalMoisture: number;
  averageMoisture: number;
  totalLand: number;
  zones: Array<{
    zone_id: string;
    moisture: number;
  }>;
}

export interface DashboardSummary {
  moisture: MoistureMetrics;
  alarms: any;
  ph: any;
  waterUsage: any;
}
```

---

## 🚀 Démarrage rapide

### 1. Vérifier que le backend est démarré
```bash
cd backend
uvicorn main:app --reload
# Backend accessible sur http://127.0.0.1:8000
```

### 2. Tester l'API avec curl
```bash
# Récupérer l'historique
curl http://127.0.0.1:8000/history

# Récupérer la configuration
curl http://127.0.0.1:8000/configuration

# Récupérer le dashboard complet
curl http://127.0.0.1:8000/dashboard/summary
```

### 3. Créer le projet frontend
```bash
# React + TypeScript
npm create vite@latest smartirrig-frontend -- --template react-ts
cd smartirrig-frontend
npm install axios chart.js react-chartjs-2

# Ou Vue + TypeScript
npm create vite@latest smartirrig-frontend -- --template vue-ts
cd smartirrig-frontend
npm install axios chart.js vue-chartjs
```

### 4. Configurer CORS si nécessaire
Le backend accepte déjà les requêtes depuis:
- http://localhost:3000
- http://localhost:3001

Si vous utilisez un autre port, modifiez dans `backend/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:VOTRE_PORT"],
    ...
)
```

---

## 📝 Checklist développement

### Phase 1: Setup (1-2 jours)
- [ ] Créer le projet frontend
- [ ] Installer les dépendances
- [ ] Configurer le service API
- [ ] Définir les types TypeScript
- [ ] Tester la connexion backend
- [ ] Créer la structure de navigation

### Phase 2: Dashboard (2-3 jours)
- [ ] Créer les métric cards
- [ ] Implémenter les graphiques (Chart.js)
- [ ] Auto-refresh toutes les 5s
- [ ] Indicateur de connexion
- [ ] Responsive design

### Phase 3: Contrôle & Config (2 jours)
- [ ] Page contrôle manuel
- [ ] Toggle valve avec confirmation
- [ ] Contrôle météo
- [ ] Formulaire configuration
- [ ] Validation et sauvegarde

### Phase 4: Statistiques (2 jours)
- [ ] Page statistiques eau
- [ ] Graphiques comparatifs
- [ ] Export CSV/JSON
- [ ] Prédictions ML

### Phase 5: Alertes & Logs (1 jour)
- [ ] Liste des alertes
- [ ] Filtres
- [ ] Notifications toast
- [ ] Clear logs

### Phase 6: Réservoir (1 jour)
- [ ] Visualisation jauge
- [ ] Contrôles de remplissage
- [ ] Alertes niveau

### Phase 7: Polish (1-2 jours)
- [ ] Dark mode
- [ ] Loading states
- [ ] Error handling
- [ ] Tests unitaires
- [ ] Documentation

---

## 🐛 Debugging

### Backend non accessible
```bash
# Vérifier que le backend tourne
curl http://127.0.0.1:8000/

# Démarrer le backend
cd backend
uvicorn main:app --reload
```

### Erreurs CORS
```javascript
// Vérifier que l'URL est correcte
const API_BASE_URL = 'http://127.0.0.1:8000'; // PAS localhost:8000
```

### Données vides
```bash
# Lancer la simulation pour générer des données
python simulation/simulation_backend.py
```

---

## 📚 Ressources utiles

### Documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [MongoDB Docs](https://www.mongodb.com/docs/)
- [Chart.js](https://www.chartjs.org/)
- [React Query](https://tanstack.com/query/latest)

### Outils
- [Postman](https://www.postman.com/) - Tester l'API
- [MongoDB Compass](https://www.mongodb.com/products/compass) - Explorer la DB
- [React DevTools](https://react.dev/learn/react-developer-tools)

---

## 👥 Support

Pour toute question :
1. Vérifier les logs backend
2. Tester les endpoints avec curl/Postman
3. Vérifier la console navigateur (F12)
4. Consulter ce document

---

**📅 Dernière mise à jour**: 27 février 2026
**🔧 Version backend**: 2.0
**📊 Nombre d'endpoints**: 25+



j'ai modifier ce fichier aussi 