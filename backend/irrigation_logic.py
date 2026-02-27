def irrigation_decision(
    soil_moisture: float, 
    pump_was_active: bool = False, 
    rainfall: bool = False, 
    seuil_bas: int = 40, 
    seuil_haut: int = 70,
    temperature: float = 25.0,
    wind_speed: float = 5.0,
    light_intensity: int = 0,
    heure: int = 12
) -> dict:
    """
    🧠 ALGORITHME D'IRRIGATION INTELLIGENT MULTI-FACTEURS
    
    Prend en compte TOUS les facteurs environnementaux pour décider de l'irrigation optimale :
    
    FACTEURS ANALYSÉS :
    - 💧 Humidité du sol : Critère principal (seuils configurables)
    - 🌧️ Pluie : Priorité absolue - arrêt immédiat
    - 🌡️ Température : Ajuste les seuils selon la chaleur
    - 🌬️ Vent : Bloque si trop venteux (évaporation rapide)
    - ☀️ Lumière : Préfère irrigation tôt matin/soir
    - ⏰ Heure : Évite les heures chaudes (10h-16h)
    
    LOGIQUE DE DÉCISION :
    1. Si pluie → ARRÊT IMMÉDIAT
    2. Si vent > 25 km/h → BLOCAGE (gaspillage d'eau)
    3. Si plein soleil + chaleur → REPORT (évaporation excessive)
    4. Si conditions optimales → Irrigation selon humidité ajustée
    """
    
    # ⛔ RÈGLE PRIORITAIRE #1 : ARRÊT IMMÉDIAT si pluie
    if rainfall:
        if pump_was_active:
            return {
                "pump": False,
                "message": f"🌧️ Pluie détectée → Irrigation ARRÊTÉE (humidité: {soil_moisture:.1f}%)"
            }
        else:
            return {
                "pump": False,
                "message": f"🌧️ Pluie active → Pas d'irrigation nécessaire"
            }
    
    # 🌬️ RÈGLE #2 : BLOCAGE si vent trop fort (évaporation excessive)
    if wind_speed > 25:
        return {
            "pump": False,
            "message": f"🌬️ Vent fort ({wind_speed:.1f} km/h) → Irrigation reportée (évaporation rapide)"
        }
    
    # 🌡️ AJUSTEMENT DES SEUILS SELON LA TEMPÉRATURE
    # Plus il fait chaud, plus on irrigue tôt (avant que le sol soit trop sec)
    seuil_bas_ajuste = seuil_bas
    seuil_haut_ajuste = seuil_haut
    
    if temperature > 30:
        # Très chaud : irriguer plus tôt (+5% au seuil bas)
        seuil_bas_ajuste = seuil_bas + 5
        seuil_haut_ajuste = seuil_haut + 5
    elif temperature > 35:
        # Extrêmement chaud : irriguer beaucoup plus tôt (+10%)
        seuil_bas_ajuste = seuil_bas + 10
        seuil_haut_ajuste = seuil_haut + 10
    elif temperature < 15:
        # Froid : réduire l'irrigation (-5%)
        seuil_bas_ajuste = max(20, seuil_bas - 5)
        seuil_haut_ajuste = max(50, seuil_haut - 5)
    
    # ☀️ + ⏰ RÈGLE #3 : ÉVITER irrigation en plein soleil + chaleur
    # Lumière > 40000 lux = plein soleil, 10h-16h = heures chaudes
    if light_intensity > 40000 and 10 <= heure <= 16 and temperature > 28:
        # Exception : sol vraiment très sec (urgence)
        if soil_moisture < (seuil_bas - 10):
            pass  # On irrigue quand même en urgence
        elif pump_was_active:
            # Si déjà en cours, on continue jusqu'au seuil haut
            pass
        else:
            return {
                "pump": False,
                "message": f"☀️ Plein soleil + chaleur → Irrigation reportée (évaporation excessive, heure non optimale)"
            }
    
    # 💧 DÉCISION BASÉE SUR L'HUMIDITÉ (avec seuils ajustés)
    
    # Si pompe déjà active : continuer jusqu'au seuil haut ajusté
    if pump_was_active:
        if soil_moisture >= seuil_haut_ajuste:
            return {
                "pump": False,
                "message": f"✅ Objectif atteint ({soil_moisture:.1f}% ≥ {seuil_haut_ajuste:.0f}%) → Irrigation OFF"
            }
        else:
            return {
                "pump": True,
                "message": f"💦 Irrigation en cours ({soil_moisture:.1f}% → objectif {seuil_haut_ajuste:.0f}%)"
            }
    
    # Pompe inactive : vérifier s'il faut démarrer
    if soil_moisture < seuil_bas_ajuste:
        # Conditions optimales pour démarrer
        return {
            "pump": True,
            "message": f"💦 Sol sec ({soil_moisture:.1f}% < {seuil_bas_ajuste:.0f}%) → Irrigation ON (T:{temperature:.1f}°C, Vent:{wind_speed:.1f}km/h)"
        }
    else:
        return {
            "pump": False,
            "message": f"✓ Humidité suffisante ({soil_moisture:.1f}%) → Irrigation OFF"
        }
