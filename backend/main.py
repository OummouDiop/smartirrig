from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import db
from models import SensorData, SensorDataCreate, IrrigationDecision, ValveState, ValveToggleRequest, ValveToggleResponse
from irrigation_logic import irrigation_decision
import joblib
import numpy as np
import os

# Plus besoin de créer les tables avec MongoDB

# Variable globale pour stocker la météo forcée
forced_weather = {"condition": None, "rain_intensity": None}

# Variable globale pour gérer la synchronisation avec la simulation
from datetime import datetime, timedelta
simulation_control = {
    "manual_data_received": False,
    "last_manual_timestamp": None
}

# 📊 HISTORIQUE DES DONNÉES (24 dernières heures)
historique_24h = []
MAX_HISTORIQUE = 288  # 24h * 12 points/heure (1 point toutes les 5 minutes)

# ⚙️ CONFIGURATION DYNAMIQUE (sans redémarrage)
configuration_dynamique = {
    "type_plante": "tomates",
    "saison": "ete",
    "mode": "eco",  # eco ou intensif
    "seuil_declenchement": 50,
    "seuil_arret": 80
}

# ⚠️ SYSTÈME D'ALERTES ET LOGS
alertes_logs = []
MAX_LOGS = 100  # Garder les 100 derniers événements

# 💧 STATISTIQUES DE CONSOMMATION D'EAU ET PERFORMANCE
statistiques_eau = {
    "eau_utilisee_intelligente": 0.0,  # Litres avec système intelligent
    "eau_traditionnelle_estimee": 0.0,  # Litres qu'on aurait utilisé en mode traditionnel
    "temps_irrigation_intelligent": 0,  # Minutes d'irrigation intelligente
    "temps_irrigation_traditionnel": 0,  # Minutes qu'on aurait irrigué en mode traditionnel
    "nombre_cycles_evites": 0,  # Cycles d'irrigation évités grâce à la pluie
    "date_debut": None,  # Date de début du tracking
    "economie_pourcentage": 0.0  # Pourcentage d'eau économisée
}

# 🚰 RÉSERVOIR D'EAU - MONITORING DU NIVEAU
reservoir_eau = {
    "capacite_totale": 1000.0,  # Capacité maximale en litres
    "niveau_actuel": 200.0,      # Niveau actuel en litres (20% au démarrage)
    "pourcentage": 20.0,         # Pourcentage du réservoir
    "seuil_alerte_critique": 10.0,  # Alerte critique à 10%
    "seuil_alerte_bas": 25.0,       # Alerte basse à 25%
    "seuil_alerte_moyen": 50.0,     # Alerte moyenne à 50%
    "derniere_alerte": None,         # Timestamp de la dernière alerte envoyée
    "irrigation_bloquee": False      # Bloquer irrigation si niveau trop bas
}

# Charger le modèle de prédiction au démarrage
import os
MODEL_PATH = os.path.join(os.path.dirname(__file__), "soil_moisture_model_v2.pkl")
print(f"📂 Chemin du modèle: {MODEL_PATH}")
print(f"📂 Chemin absolu: {os.path.abspath(MODEL_PATH)}")
print(f"✅ Fichier existe: {os.path.exists(MODEL_PATH)}")

soil_moisture_pipeline = None

try:
    if os.path.exists(MODEL_PATH):
        soil_moisture_pipeline = joblib.load(MODEL_PATH)
        # Le pipeline est un dict avec scaler + model + metadata
        if isinstance(soil_moisture_pipeline, dict):
            print(f"✅ Pipeline de prédiction chargé: version {soil_moisture_pipeline.get('version', 'unknown')}")
        else:
            print(f"✅ Modèle de prédiction chargé avec succès !")
    else:
        print(f"❌ Fichier modèle non trouvé: {MODEL_PATH}")
except Exception as e:
    print(f"❌ Erreur lors du chargement du modèle: {e}")
    import traceback
    traceback.print_exc()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




# ---------- ROUTES ----------

@app.get("/")
def home():
    return {"message": "IoT Irrigation Backend Running"}



@app.post("/send-data", response_model=IrrigationDecision)
def receive_sensor_data(data: SensorDataCreate, is_manual: bool = False):
    global simulation_control, historique_24h, alertes_logs, configuration_dynamique
    
    # Préparer le document à insérer
    from datetime import datetime, timedelta
    timestamp_now = datetime.utcnow()
    record_dict = {
        "zone_id": data.zone_id,
        "humidity": data.humidity,
        "temperature": data.temperature,
        "soil_moisture": data.soil_moisture,
        "soil_moisture_10cm": data.soil_moisture_10cm or data.soil_moisture * 0.9,
        "soil_moisture_30cm": data.soil_moisture_30cm or data.soil_moisture,
        "soil_moisture_60cm": data.soil_moisture_60cm or data.soil_moisture * 1.1,
        "soil_ph": data.soil_ph or 6.5,
        "light": data.light or 450.0,
        "wind_speed": data.wind_speed or 8.0,
        "rainfall": data.rainfall,
        "rainfall_intensity": data.rainfall_intensity,
        "created_at": timestamp_now,
        "source": "manual" if is_manual else "auto"
    }
    result = db["sensor_data"].insert_one(record_dict)
    record_id = result.inserted_id
    
    # 📊 AJOUTER À L'HISTORIQUE 24H
    point_historique = {
        "timestamp": int(timestamp_now.timestamp() * 1000),
        "temperature": data.temperature,
        "humidity": data.humidity,
        "soil_moisture": data.soil_moisture,
        "soil_moisture_10cm": data.soil_moisture_10cm or data.soil_moisture * 0.9,
        "soil_moisture_30cm": data.soil_moisture_30cm or data.soil_moisture,
        "soil_moisture_60cm": data.soil_moisture_60cm or data.soil_moisture * 1.1,
        "soil_ph": data.soil_ph or 6.5,
        "light": data.light or 450.0,
        "wind_speed": data.wind_speed or 8.0,
        "rainfall": data.rainfall
    }
    historique_24h.append(point_historique)
    
    # Limiter la taille (garder les 24 dernières heures)
    if len(historique_24h) > MAX_HISTORIQUE:
        historique_24h.pop(0)

    # 🧠 DÉCISION D'IRRIGATION INTELLIGENTE MULTI-FACTEURS
    # Calculer l'heure actuelle (0-23)
    heure_actuelle = timestamp_now.hour
    
    # Appel de l'algorithme avec TOUS les facteurs environnementaux
    decision = irrigation_decision(
        soil_moisture=data.soil_moisture, 
        pump_was_active=data.pump_was_active, 
        rainfall=data.rainfall,
        seuil_bas=configuration_dynamique["seuil_declenchement"],
        seuil_haut=configuration_dynamique["seuil_arret"],
        temperature=data.temperature,
        wind_speed=data.wind_speed or 0,
        light_intensity=int(data.light or 0),
        heure=heure_actuelle
    )
    
    # 🚰 VÉRIFIER LE NIVEAU DU RÉSERVOIR - BLOQUER SI TROP BAS
    global reservoir_eau
    if reservoir_eau["pourcentage"] < reservoir_eau["seuil_alerte_critique"]:
        # Niveau critique : bloquer toute irrigation
        decision['pump'] = False
        reservoir_eau["irrigation_bloquee"] = True
        decision['message'] = f"🚫 Irrigation BLOQUÉE - Réservoir critique ({reservoir_eau['pourcentage']:.1f}%)"
    elif reservoir_eau["pourcentage"] < reservoir_eau["seuil_alerte_bas"] and decision['pump']:
        # Niveau bas : permettre mais alerter
        heure = timestamp_now.strftime("%H:%M")
        if reservoir_eau["derniere_alerte"] is None or \
           (timestamp_now.timestamp() - reservoir_eau["derniere_alerte"]) > 300:  # Alerte max toutes les 5 min
            alertes_logs.append({
                "timestamp": int(timestamp_now.timestamp() * 1000),
                "time": heure,
                "message": f"{heure} - ⚠️ ALERTE: Niveau d'eau bas ({reservoir_eau['pourcentage']:.1f}%) - Remplissage recommandé",
                "type": "alert_reservoir_bas",
                "zone_id": data.zone_id
            })
            reservoir_eau["derniere_alerte"] = timestamp_now.timestamp()
    else:
        reservoir_eau["irrigation_bloquee"] = False

    # Mettre à jour l'état de la valve dans la base de données
    valve_state = db["valve_states"].find_one({"zone_id": data.zone_id})
    previous_pump_state = valve_state.get("is_open", False) if valve_state else False
    
    if not valve_state:
        db["valve_states"].insert_one({"zone_id": data.zone_id, "is_open": decision['pump']})
    else:
        db["valve_states"].update_one({"zone_id": data.zone_id}, {"$set": {"is_open": decision['pump']}})
    
    # ⚠️ CRÉER DES LOGS D'ÉVÉNEMENTS
    if previous_pump_state != decision['pump']:
        heure = timestamp_now.strftime("%H:%M")
        if decision['pump']:
            # Déterminer la cause
            if data.soil_moisture < configuration_dynamique["seuil_declenchement"]:
                cause = "Sécheresse"
            else:
                cause = "Décision automatique"
            log_message = f"{heure} - Début arrosage (Cause: {cause})"
            log_type = "irrigation_start"
        else:
            # Déterminer la cause d'arrêt
            if data.rainfall:
                cause = "Pluie détectée"
                # 💧 Incrémenter les cycles évités grâce à la pluie
                statistiques_eau["nombre_cycles_evites"] += 1
            elif data.soil_moisture >= configuration_dynamique["seuil_arret"]:
                cause = "Humidité suffisante"
            else:
                cause = "Décision automatique"
            log_message = f"{heure} - Arrêt arrosage (Cause: {cause})"
            log_type = "irrigation_stop"
        
        alertes_logs.append({
            "timestamp": int(timestamp_now.timestamp() * 1000),
            "time": heure,
            "message": log_message,
            "type": log_type,
            "zone_id": data.zone_id
        })
        
        # Limiter la taille des logs
        if len(alertes_logs) > MAX_LOGS:
            alertes_logs.pop(0)
    
    # 💧 TRACKING DE LA CONSOMMATION D'EAU
    if statistiques_eau["date_debut"] is None:
        statistiques_eau["date_debut"] = timestamp_now.isoformat()
    
    # Estimation : 1 cycle = ~5 min, débit moyen = 10L/min
    DEBIT_MOYEN = 10.0  # Litres par minute
    INTERVALLE_MINUTES = 0.083  # 5 secondes = 0.083 min (temps entre chaque appel)
    
    # Si irrigation active (système intelligent)
    if decision['pump']:
        eau_consommee = DEBIT_MOYEN * INTERVALLE_MINUTES
        statistiques_eau["eau_utilisee_intelligente"] += eau_consommee
        statistiques_eau["temps_irrigation_intelligent"] += INTERVALLE_MINUTES
        
        # 🚰 DÉDUIRE DU RÉSERVOIR
        reservoir_eau["niveau_actuel"] -= eau_consommee
        if reservoir_eau["niveau_actuel"] < 0:
            reservoir_eau["niveau_actuel"] = 0
        reservoir_eau["pourcentage"] = (reservoir_eau["niveau_actuel"] / reservoir_eau["capacite_totale"]) * 100
    
    # Système traditionnel : arrose toujours si humidité < 60%, sans tenir compte de la pluie
    arrosage_traditionnel = data.soil_moisture < 60
    if arrosage_traditionnel:
        statistiques_eau["eau_traditionnelle_estimee"] += DEBIT_MOYEN * INTERVALLE_MINUTES
        statistiques_eau["temps_irrigation_traditionnel"] += INTERVALLE_MINUTES
    
    # Calculer le pourcentage d'économie
    if statistiques_eau["eau_traditionnelle_estimee"] > 0:
        economie = statistiques_eau["eau_traditionnelle_estimee"] - statistiques_eau["eau_utilisee_intelligente"]
        statistiques_eau["economie_pourcentage"] = (economie / statistiques_eau["eau_traditionnelle_estimee"]) * 100
    else:
        statistiques_eau["economie_pourcentage"] = 0.0
    
    # Alerte vent fort
    if data.wind_speed and data.wind_speed > 25:
        heure = timestamp_now.strftime("%H:%M")
        alertes_logs.append({
            "timestamp": int(timestamp_now.timestamp() * 1000),
            "time": heure,
            "message": f"{heure} - Alerte: Vent fort ({data.wind_speed:.1f} km/h), irrigation reportée",
            "type": "alert_wind",
            "zone_id": data.zone_id
        })
        if len(alertes_logs) > MAX_LOGS:
            alertes_logs.pop(0)

    return decision


# Nouvelle route pour la simulation manuelle
@app.post("/send-manual-data", response_model=IrrigationDecision)
def receive_manual_data(data: SensorDataCreate):
    global simulation_control
    
    # Marquer qu'on a reçu des données manuelles
    simulation_control["manual_data_received"] = True
    simulation_control["last_manual_timestamp"] = datetime.utcnow()
    
    # Traiter les données manuelles normalement avec is_manual=True
    return receive_sensor_data(data, is_manual=True)


# Route pour vérifier et récupérer les dernières données
@app.get("/simulation-status")
def get_simulation_status():
    global simulation_control
    
    # Récupérer les dernières données pour synchroniser la simulation (tri par created_at décroissant)
    latest_records = list(db["sensor_data"].find().sort("created_at", -1).limit(1))
    latest_data = latest_records[0] if latest_records else None
    valve_state = db["valve_states"].find_one({"zone_id": "zone-1"})
    
    response_data = {
        "manual_data_received": False,
        "latest_data": None
    }
    
    # Vérifier si les dernières données sont manuelles ET récentes (moins de 10 secondes)
    if latest_data:
        source = latest_data.get("source", "auto")
        created_at = latest_data.get("created_at", datetime.utcnow())
        time_diff = datetime.utcnow() - created_at
        
        print(f"🔍 /simulation-status: source={source}, age={time_diff.total_seconds():.1f}s")
        
        if source == "manual" and time_diff.total_seconds() < 10:
            response_data["manual_data_received"] = True
            response_data["latest_data"] = {
                "soil_moisture_10cm": latest_data.get("soil_moisture_10cm", 45),
                "soil_moisture_30cm": latest_data.get("soil_moisture_30cm", 55),
                "soil_moisture_60cm": latest_data.get("soil_moisture_60cm", 65),
                "temperature": latest_data.get("temperature", 25),
                "humidity": latest_data.get("humidity", 60),
                "pump_active": valve_state.get("is_open", False) if valve_state else False
            }
            print(f"✅ Données manuelles détectées! Envoi pour sync: {latest_data.get('soil_moisture_10cm')}%, {latest_data.get('soil_moisture_30cm')}%, {latest_data.get('soil_moisture_60cm')}%")
    
    return response_data


@app.get("/history")
def get_history(zone_id: str = None):
    query = {}
    if zone_id:
        query["zone_id"] = zone_id
    # Trier par created_at décroissant pour avoir les plus récents en premier
    records = list(db["sensor_data"].find(query).sort("created_at", -1).limit(100))
    result = []
    for r in records:
        created_at = r.get("created_at")
        # Conversion du champ created_at en timestamp (ms)
        timestamp = None
        if created_at:
            try:
                # Pour les objets datetime natifs
                timestamp = int(created_at.timestamp() * 1000)
            except Exception:
                # Pour les chaînes ISO (au cas où)
                from dateutil import parser
                try:
                    dt = parser.isoparse(str(created_at))
                    timestamp = int(dt.timestamp() * 1000)
                except Exception:
                    timestamp = None
        result.append({
            "id": str(r.get("_id")),
            "zone_id": r.get("zone_id"),
            "timestamp": timestamp,
            "moisture": r.get("soil_moisture"),
            "temperature": r.get("temperature"),
            "humidity": r.get("humidity"),
            "soilMoisture10cm": r.get("soil_moisture_10cm", r.get("soil_moisture", 0) * 0.9),
            "soilMoisture30cm": r.get("soil_moisture_30cm", r.get("soil_moisture")),
            "soilMoisture60cm": r.get("soil_moisture_60cm", r.get("soil_moisture", 0) * 1.1),
            "light": r.get("light", 450.0),
            "windSpeed": r.get("wind_speed", 8.0),
            "rainfall": r.get("rainfall"),
            "rainfallIntensity": r.get("rainfall_intensity"),
            "created_at": str(created_at) if created_at else None
        })
    return result



@app.post("/toggle-valve", response_model=ValveToggleResponse)
def toggle_valve(request: ValveToggleRequest):
    """
    Contrôle manuel de la vanne d'irrigation pour une zone.
    Active ou désactive la pompe/électrovanne.
    """
    valve_state = db["valve_states"].find_one({"zone_id": request.zone_id})
    if not valve_state:
        db["valve_states"].insert_one({"zone_id": request.zone_id, "is_open": request.valve_open})
    else:
        db["valve_states"].update_one({"zone_id": request.zone_id}, {"$set": {"is_open": request.valve_open}})

    status = "ouverte" if request.valve_open else "fermee"
    action = "IRRIGATION ACTIVEE" if request.valve_open else "IRRIGATION ARRETEE"

    return ValveToggleResponse(
        zone_id=request.zone_id,
        valve_open=request.valve_open,
        message=f"{action} - Vanne {status} pour {request.zone_id}"
    )



@app.get("/valve-state/{zone_id}")
def get_valve_state(zone_id: str):
    """
    Récupère l'état actuel de la vanne pour une zone.
    """
    valve_state = db["valve_states"].find_one({"zone_id": zone_id})
    if not valve_state:
        return {
            "zone_id": zone_id,
            "valve_open": False,
            "message": "Aucun état trouvé - vanne fermée par défaut"
        }
    return {
        "zone_id": valve_state.get("zone_id"),
        "valve_open": valve_state.get("is_open", False),
        "updated_at": str(valve_state.get("updated_at")) if valve_state.get("updated_at") else None
    }

@app.post("/set-weather")
def set_weather(condition: str):
    global forced_weather
    
    if condition.lower() == 'auto':
        forced_weather = {"condition": None, "rain_intensity": None}
        return {"message": "Météo en mode automatique", "condition": "auto"}
    elif condition.lower() == 'sunny':
        forced_weather = {"condition": "sunny", "rain_intensity": None}
        return {"message": "☀️ Temps forcé : Ensoleillé", "condition": "sunny"}
    elif condition.lower() == 'cloudy':
        forced_weather = {"condition": "cloudy", "rain_intensity": None}
        return {"message": "☁️ Temps forcé : Nuageux", "condition": "cloudy"}
    elif condition.lower() == 'rainy':
        forced_weather = {"condition": "rainy", "rain_intensity": "moderate"}
        return {"message": "🌧️ Temps forcé : Pluvieux", "condition": "rainy"}
    else:
        return {"error": "Condition invalide"}

@app.get("/get-weather")
def get_weather():
    return forced_weather


def get_soil_moisture_prediction(zone_id: str):
    """
    Retourne la prédiction du modèle pour l'humidité du sol.
    Utilise les 5 derniers points de données (24h d'historique).
    """
    if soil_moisture_pipeline is None:
        return {
            "prediction": None,
            "error": "Modèle non disponible",
            "confidence": None
        }
    
    try:
        # Récupérer les 5 derniers points (les plus récents d'abord)
        records = list(db["sensor_data"].find({"zone_id": zone_id}).sort("created_at", -1).limit(5))
        
        if len(records) < 5:
            return {
                "prediction": None,
                "error": f"Pas assez de données historiques ({len(records)}/5 points)",
                "confidence": None
            }
        
        # Inverser pour avoir l'ordre chronologique (plus ancien → plus récent)
        records = records[::-1]
        
        # Extraire les features (10 capteurs par point)
        features_list = []
        for record in records:
            point_features = [
                float(record.get("humidity", 0)),
                float(record.get("temperature", 0)),
                float(record.get("soil_moisture", 0)),
                float(record.get("soil_moisture_10cm", 0)),
                float(record.get("soil_moisture_30cm", 0)),
                float(record.get("soil_moisture_60cm", 0)),
                float(record.get("light", 0)),
                float(record.get("wind_speed", 0)),
                float(record.get("rainfall", 0)) if isinstance(record.get("rainfall"), (int, float)) else (1.0 if record.get("rainfall") else 0.0),
                float(record.get("rainfall_intensity", 0)) if isinstance(record.get("rainfall_intensity"), (int, float)) else 0.0,
            ]
            features_list.extend(point_features)
        
        # Convertir en array (50 features total : 5 points × 10 capteurs)
        X = np.array(features_list).reshape(1, -1)
        
        # Faire la prédiction selon le format du pipeline
        if isinstance(soil_moisture_pipeline, dict):
            # Nouveau format avec scaler
            scaler = soil_moisture_pipeline['scaler']
            model = soil_moisture_pipeline['model']
            X_scaled = scaler.transform(X)
            prediction = model.predict(X_scaled)[0]
        else:
            # Ancien format (modèle seul)
            prediction = soil_moisture_pipeline.predict(X)[0]
        
        # Calculer une confiance approximative basée sur la variance des prédictions
        confidence = None
        if isinstance(soil_moisture_pipeline, dict) and 'model' in soil_moisture_pipeline:
            model = soil_moisture_pipeline['model']
            if hasattr(model, 'estimators_'):
                # Pour RandomForest, calculer la variance entre les arbres
                try:
                    predictions = [tree.predict(X_scaled if isinstance(soil_moisture_pipeline, dict) else X)[0] 
                                 for tree in model.estimators_[:50]]  # Utiliser 50 arbres pour la vitesse
                    variance = np.std(predictions)
                    # Confidence inversement proportionnelle à la variance (max 100%)
                    confidence = float(max(0, min(100, 100 - variance)))
                except:
                    pass
        
        return {
            "prediction": float(round(prediction, 2)),
            "error": None,
            "confidence": confidence,
            "num_samples_used": len(records)
        }
        
    except Exception as e:
        return {
            "prediction": None,
            "error": str(e),
            "confidence": None
        }


@app.get("/predict-soil-moisture/{zone_id}")
def predict_soil_moisture(zone_id: str):
    """
    Retourne la prédiction de l'humidité du sol pour les prochaines heures.
    Utilise les 5 derniers points (24h d'historique).
    """
    return get_soil_moisture_prediction(zone_id)


# ========== NOUVELLES ROUTES ==========

@app.get("/historique-24h")
def get_historique_24h():
    """
    📊 Retourne l'historique des 24 dernières heures
    """
    global historique_24h
    return {
        "data": historique_24h,
        "total_points": len(historique_24h),
        "periode": "24 heures"
    }


@app.get("/configuration")
def get_configuration():
    """
    ⚙️ Retourne la configuration dynamique actuelle
    """
    global configuration_dynamique
    return configuration_dynamique


@app.post("/configuration")
def update_configuration(config: dict):
    """
    ⚙️ Met à jour la configuration dynamique SANS redémarrage
    Accepte: type_plante, saison, mode, seuil_declenchement, seuil_arret
    """
    global configuration_dynamique, alertes_logs
    
    # Mettre à jour les valeurs fournies
    if "type_plante" in config:
        configuration_dynamique["type_plante"] = config["type_plante"]
    if "saison" in config:
        configuration_dynamique["saison"] = config["saison"]
    if "mode" in config:
        configuration_dynamique["mode"] = config["mode"]
    if "seuil_declenchement" in config:
        configuration_dynamique["seuil_declenchement"] = config["seuil_declenchement"]
    if "seuil_arret" in config:
        configuration_dynamique["seuil_arret"] = config["seuil_arret"]
    
    # Créer un log de changement de configuration
    timestamp_now = datetime.utcnow()
    heure = timestamp_now.strftime("%H:%M")
    log_message = f"{heure} - Configuration modifiée: {config.get('type_plante', 'N/A')} / {config.get('saison', 'N/A')} / {config.get('mode', 'N/A')}"
    
    alertes_logs.append({
        "timestamp": int(timestamp_now.timestamp() * 1000),
        "time": heure,
        "message": log_message,
        "type": "config_change",
        "zone_id": "system"
    })
    
    if len(alertes_logs) > MAX_LOGS:
        alertes_logs.pop(0)
    
    return {
        "success": True,
        "message": "Configuration mise à jour sans redémarrage",
        "config": configuration_dynamique
    }


@app.get("/alertes-logs")
def get_alertes_logs(limit: int = 20):
    """
    ⚠️ Retourne les alertes et logs des événements
    """
    global alertes_logs
    # Retourner les plus récents en premier
    return {
        "logs": list(reversed(alertes_logs[-limit:])),
        "total": len(alertes_logs)
    }


@app.get("/statistiques-eau")
def get_statistiques_eau():
    """
    💧 Retourne les statistiques de consommation d'eau et performance
    """
    global statistiques_eau
    
    # Calculer les économies en litres
    economie_litres = statistiques_eau["eau_traditionnelle_estimee"] - statistiques_eau["eau_utilisee_intelligente"]
    
    # Calculer le temps d'économie
    temps_economise = statistiques_eau["temps_irrigation_traditionnel"] - statistiques_eau["temps_irrigation_intelligent"]
    
    return {
        "eau_intelligente": round(statistiques_eau["eau_utilisee_intelligente"], 2),
        "eau_traditionnelle": round(statistiques_eau["eau_traditionnelle_estimee"], 2),
        "economie_litres": round(economie_litres, 2),
        "economie_pourcentage": round(statistiques_eau["economie_pourcentage"], 1),
        "temps_irrigation_intelligent_minutes": round(statistiques_eau["temps_irrigation_intelligent"], 1),
        "temps_irrigation_traditionnel_minutes": round(statistiques_eau["temps_irrigation_traditionnel"], 1),
        "temps_economise_minutes": round(temps_economise, 1),
        "cycles_evites_pluie": statistiques_eau["nombre_cycles_evites"],
        "date_debut": statistiques_eau["date_debut"]
    }


@app.post("/statistiques-eau/reset")
def reset_statistiques_eau():
    """
    💧 Réinitialiser les statistiques de consommation d'eau
    """
    global statistiques_eau
    statistiques_eau = {
        "eau_utilisee_intelligente": 0.0,
        "eau_traditionnelle_estimee": 0.0,
        "temps_irrigation_intelligent": 0,
        "temps_irrigation_traditionnel": 0,
        "nombre_cycles_evites": 0,
        "date_debut": None,
        "economie_pourcentage": 0.0
    }
    return {"message": "Statistiques réinitialisées avec succès"}


@app.get("/reservoir-eau")
def get_reservoir_eau():
    """
    🚰 Retourne l'état du réservoir d'eau
    """
    global reservoir_eau
    
    # Déterminer le statut
    if reservoir_eau["pourcentage"] < reservoir_eau["seuil_alerte_critique"]:
        statut = "critique"
        message = "🚨 CRITIQUE - Remplissage URGENT"
    elif reservoir_eau["pourcentage"] < reservoir_eau["seuil_alerte_bas"]:
        statut = "bas"
        message = "⚠️ Niveau bas - Remplissage recommandé"
    elif reservoir_eau["pourcentage"] < reservoir_eau["seuil_alerte_moyen"]:
        statut = "moyen"
        message = "ℹ️ Niveau moyen"
    else:
        statut = "bon"
        message = "✅ Niveau optimal"
    
    return {
        "capacite_totale": reservoir_eau["capacite_totale"],
        "niveau_actuel": round(reservoir_eau["niveau_actuel"], 2),
        "pourcentage": round(reservoir_eau["pourcentage"], 1),
        "statut": statut,
        "message": message,
        "irrigation_bloquee": reservoir_eau["irrigation_bloquee"],
        "seuils": {
            "critique": reservoir_eau["seuil_alerte_critique"],
            "bas": reservoir_eau["seuil_alerte_bas"],
            "moyen": reservoir_eau["seuil_alerte_moyen"]
        }
    }


@app.post("/reservoir-eau/remplir")
def remplir_reservoir(litres: float = None):
    """
    🚰 Remplir le réservoir (quantité en litres, ou remplissage complet si non spécifié)
    """
    global reservoir_eau
    
    if litres is None:
        # Remplissage complet
        reservoir_eau["niveau_actuel"] = reservoir_eau["capacite_totale"]
        message = f"Réservoir rempli à 100% ({reservoir_eau['capacite_totale']}L)"
    else:
        reservoir_eau["niveau_actuel"] = min(
            reservoir_eau["niveau_actuel"] + litres,
            reservoir_eau["capacite_totale"]
        )
        message = f"Ajout de {litres}L au réservoir"
    
    reservoir_eau["pourcentage"] = (reservoir_eau["niveau_actuel"] / reservoir_eau["capacite_totale"]) * 100
    reservoir_eau["irrigation_bloquee"] = False
    reservoir_eau["derniere_alerte"] = None
    
    return {
        "message": message,
        "niveau_actuel": round(reservoir_eau["niveau_actuel"], 2),
        "pourcentage": round(reservoir_eau["pourcentage"], 1)
    }


@app.delete("/alertes-logs")
def clear_alertes_logs():
    """
    🗑️ Efface tous les logs (utile pour les tests)
    """
    global alertes_logs
    alertes_logs.clear()
    return {"success": True, "message": "Logs effacés"}


# ========================================
# 📊 NOUVEAUX ENDPOINTS DASHBOARD
# ========================================

@app.get("/dashboard/moisture-metrics")
def get_moisture_metrics():
    """
    📊 Statistiques d'humidité pour le dashboard
    Retourne: Total Moisture, Average Moisture, Total Land
    """
    # Récupérer les dernières données de toutes les zones
    from datetime import datetime, timedelta
    
    # Obtenir les données des dernières 24h pour avoir une moyenne
    time_24h_ago = datetime.utcnow() - timedelta(hours=24)
    
    recent_data = list(db["sensor_data"].find({
        "created_at": {"$gte": time_24h_ago}
    }).sort("created_at", -1))
    
    if not recent_data:
        return {
            "totalMoisture": 0,
            "averageMoisture": 0,
            "totalLand": 0,
            "zones": []
        }
    
    # Calculer les métriques par zone
    zones_data = {}
    for record in recent_data:
        zone_id = record.get("zone_id", "zone-1")
        if zone_id not in zones_data:
            zones_data[zone_id] = []
        zones_data[zone_id].append(record.get("soil_moisture", 0))
    
    # Calculer les moyennes par zone
    zone_averages = {}
    for zone_id, moistures in zones_data.items():
        zone_averages[zone_id] = sum(moistures) / len(moistures) if moistures else 0
    
    # Métriques globales
    all_moistures = [m for moistures in zones_data.values() for m in moistures]
    average_moisture = sum(all_moistures) / len(all_moistures) if all_moistures else 0
    
    # Total Moisture = moyenne pondérée de toutes les zones
    total_moisture = average_moisture
    
    # Total Land = pourcentage de zones actives/surveillées
    total_zones_possible = 3  # Comme dans l'image du dashboard
    total_land = (len(zones_data) / total_zones_possible) * 100
    
    return {
        "totalMoisture": round(total_moisture, 1),
        "averageMoisture": round(average_moisture, 1),
        "totalLand": round(total_land, 1),
        "zones": [
            {
                "zone_id": zone_id,
                "moisture": round(avg, 1)
            }
            for zone_id, avg in zone_averages.items()
        ]
    }


@app.get("/dashboard/alarm-history")
def get_alarm_history():
    """
    ⚠️ Historique des alarmes pour le graphique
    Retourne les alarmes groupées par jour de la semaine
    """
    from datetime import datetime, timedelta
    from collections import defaultdict
    
    # Obtenir les 7 derniers jours
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    
    # Filtrer les alertes des 7 derniers jours
    alarms_by_day = defaultdict(int)
    days_of_week = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    
    for alert in alertes_logs:
        alert_timestamp = alert["timestamp"] / 1000  # Convertir ms en secondes
        alert_date = datetime.fromtimestamp(alert_timestamp)
        
        if alert_date >= week_ago:
            day_name = days_of_week[alert_date.weekday()]
            if alert["type"] in ["alert_reservoir_bas", "alert_reservoir_critique"]:
                alarms_by_day[day_name] += 1
    
    # Construire les données pour le graphique (7 jours)
    chart_data = []
    for i in range(7):
        date = now - timedelta(days=6-i)
        day_name = days_of_week[date.weekday()]
        chart_data.append({
            "day": day_name,
            "alarms": alarms_by_day.get(day_name, 0),
            "date": date.strftime("%Y-%m-%d")
        })
    
    return {
        "data": chart_data,
        "totalAlarms": sum(alarms_by_day.values())
    }


@app.get("/dashboard/ph-history")
def get_ph_history():
    """
    🧪 Historique du pH du sol pour le graphique
    Retourne les données de pH sur les dernières 24h
    """
    from datetime import datetime, timedelta
    
    # Obtenir les données des dernières 24h
    time_24h_ago = datetime.utcnow() - timedelta(hours=24)
    
    ph_data = list(db["sensor_data"].find({
        "created_at": {"$gte": time_24h_ago}
    }).sort("created_at", 1).limit(100))  # Limiter à 100 points pour le graphique
    
    if not ph_data:
        return {
            "data": [],
            "currentPh": 6.5,
            "minPh": 6.5,
            "maxPh": 6.5
        }
    
    # Formater les données pour le graphique
    chart_data = []
    ph_values = []
    
    for i, record in enumerate(ph_data):
        ph_value = record.get("soil_ph", 6.5)
        ph_values.append(ph_value)
        
        timestamp = record.get("created_at", datetime.utcnow())
        chart_data.append({
            "timestamp": int(timestamp.timestamp() * 1000),
            "time": timestamp.strftime("%H:%M"),
            "ph": round(ph_value, 2),
            "zone_id": record.get("zone_id", "zone-1")
        })
    
    return {
        "data": chart_data,
        "currentPh": round(ph_values[-1], 2) if ph_values else 6.5,
        "minPh": round(min(ph_values), 2) if ph_values else 6.5,
        "maxPh": round(max(ph_values), 2) if ph_values else 6.5,
        "avgPh": round(sum(ph_values) / len(ph_values), 2) if ph_values else 6.5
    }


@app.get("/dashboard/water-usage")
def get_water_usage():
    """
    💧 Statistiques d'utilisation d'eau par jour pour le graphique
    Retourne les données d'utilisation d'eau sur les 7 derniers jours
    """
    from datetime import datetime, timedelta
    from collections import defaultdict
    
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    
    # Récupérer tous les événements d'irrigation des 7 derniers jours
    irrigation_events = list(db["sensor_data"].find({
        "created_at": {"$gte": week_ago}
    }).sort("created_at", 1))
    
    # Grouper par jour
    daily_usage = defaultdict(float)
    DEBIT_MOYEN = 10.0  # Litres par minute
    
    for i, record in enumerate(irrigation_events):
        timestamp = record.get("created_at", now)
        day_key = timestamp.strftime("%Y-%m-%d")
        
        # Estimer la consommation basée sur les événements
        # Si on a l'information valve_active dans les records
        if i > 0:
            prev_record = irrigation_events[i-1]
            time_diff = (timestamp - prev_record.get("created_at", timestamp)).total_seconds() / 60  # en minutes
            if time_diff < 10:  # Si moins de 10 min d'écart, on compte comme irrigation continue
                daily_usage[day_key] += DEBIT_MOYEN * time_diff
    
    # Construire les données pour le graphique (7 jours)
    chart_data = []
    days_labels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    
    for i in range(7):
        date = now - timedelta(days=6-i)
        day_key = date.strftime("%Y-%m-%d")
        day_label = days_labels[date.weekday()]
        
        chart_data.append({
            "day": day_label,
            "date": day_key,
            "usage": round(daily_usage.get(day_key, 0), 1),
            "unit": "L"
        })
    
    total_usage = sum(daily_usage.values())
    
    return {
        "data": chart_data,
        "totalUsage": round(total_usage, 1),
        "averageDaily": round(total_usage / 7, 1) if total_usage > 0 else 0,
        "unit": "Litres"
    }


@app.get("/dashboard/summary")
def get_dashboard_summary():
    """
    📊 Récupère toutes les données du dashboard en une seule requête
    Optimisation pour réduire les appels API
    """
    return {
        "moisture": get_moisture_metrics(),
        "alarms": get_alarm_history(),
        "ph": get_ph_history(),
        "waterUsage": get_water_usage()
    }
