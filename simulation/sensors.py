import random
import math

class CapteurHumidite:
    """Capteur d'humidité du sol à différentes profondeurs"""
    def __init__(self, humidite_initiale, profondeur):
        self.humidite = humidite_initiale
        self.profondeur = profondeur
        self.temps_derniere_irrigation = 0
        
    def simuler(self, temps_ecoule, temperature, lumiere, vitesse_vent, est_en_irrigation, pleut):
        # Évaporation basée sur la température, lumière et vent
        taux_evaporation = (temperature - 15) * 0.1 + lumiere * 0.0001 + vitesse_vent * 0.05
        
        # Réduire l'évaporation en profondeur (le sol profond garde mieux l'eau)
        if self.profondeur == "30cm":
            taux_evaporation *= 0.5  # 50% moins d'évaporation à 30cm
        elif self.profondeur == "60cm":
            taux_evaporation *= 0.3  # 70% moins d'évaporation à 60cm
        
        # Effet de la pluie
        if pleut:
            # La pluie pénètre moins en profondeur
            if self.profondeur == "10cm":
                self.humidite += random.uniform(3, 7)
            elif self.profondeur == "30cm":
                self.humidite += random.uniform(1.5, 3.5)
            elif self.profondeur == "60cm":
                self.humidite += random.uniform(0.5, 1.5)
            
        # Effet de l'irrigation
        if est_en_irrigation:
            # Base forte pour l'irrigation
            effet_irrigation = random.uniform(8, 12)
            # L'effet diminue avec la profondeur
            if self.profondeur == "30cm":
                effet_irrigation *= 0.7
            elif self.profondeur == "60cm":
                effet_irrigation *= 0.5
            self.humidite += effet_irrigation
            
        # Évaporation naturelle (réduite)
        self.humidite -= taux_evaporation * random.uniform(0.6, 0.9)
        
        # Définir un minimum réaliste selon la profondeur (le sol ne sèche jamais complètement en profondeur)
        humidite_min = {
            "10cm": 15,   # Sol de surface peut devenir très sec
            "30cm": 25,   # Sol moyen garde un minimum d'humidité
            "60cm": 35    # Sol profond reste toujours assez humide
        }.get(self.profondeur, 0)
        
        # Limiter entre minimum et 100%
        self.humidite = max(humidite_min, min(100, self.humidite))
        
        return round(self.humidite, 1)

class CapteurTemperature:
    """Capteur de température avec variation jour/nuit et saisonnière"""
    def __init__(self):
        self.temp_actuelle = 25
        
    def simuler(self, heure, saison):
        # Température de base selon la saison
        temp_saisonniere = {
            'printemps': 20,
            'ete': 28,
            'automne': 18,
            'hiver': 12
        }
        
        base = temp_saisonniere.get(saison, 25)
        
        # Variation jour/nuit (cosinus pour cycle naturel)
        variation_journaliere = 6 * math.cos((heure - 14) * math.pi / 12)
        
        # Très petit bruit aléatoire pour réalisme
        bruit = random.uniform(-0.3, 0.3)
        
        # Température cible
        temp_cible = base + variation_journaliere + bruit
        
        # Transition douce vers la température cible (inertie thermique)
        self.temp_actuelle = self.temp_actuelle * 0.9 + temp_cible * 0.1
        
        return round(self.temp_actuelle, 1)

class CapteurLumiere:
    """Capteur de luminosité (lux)"""
    def __init__(self):
        self.lumiere_max = 80000
        self.lumiere_actuelle = 0
        
    def simuler(self, heure):
        # Cycle jour/nuit avec lever/coucher du soleil
        if 6 <= heure <= 18:
            # Jour: courbe en cloche
            facteur_lumiere = math.sin((heure - 6) * math.pi / 12)
            lumiere_cible = self.lumiere_max * facteur_lumiere
        else:
            # Nuit
            lumiere_cible = random.uniform(0, 20)
        
        # Transition douce (nuages passagers)
        self.lumiere_actuelle = self.lumiere_actuelle * 0.85 + lumiere_cible * 0.15
        
        return int(max(0, self.lumiere_actuelle))

class CapteurPluie:
    """Capteur de pluie avec intensité variable"""
    def __init__(self):
        self.pleut = False
        self.duree_pluie = 0
        
    def simuler(self):
        # Probabilité de changement de météo
        if not self.pleut:
            # 5% de chance qu'il commence à pleuvoir
            if random.random() < 0.05:
                self.pleut = True
                self.duree_pluie = random.randint(3, 10)  # 3-10 cycles
        else:
            self.duree_pluie -= 1
            if self.duree_pluie <= 0:
                self.pleut = False
                
        # Intensité de la pluie
        if self.pleut:
            intensite = random.choice(['légère', 'modérée', 'forte'])
        else:
            intensite = None
            
        return self.pleut, intensite

class CapteurVent:
    """Capteur de vitesse du vent"""
    def __init__(self):
        self.vitesse_actuelle = 5
        
    def simuler(self):
        # Variation douce autour de la vitesse actuelle
        variation = random.uniform(-0.5, 0.5)
        self.vitesse_actuelle += variation
        
        # Garder dans une plage réaliste (0-15 km/h normalement, rafales occasionnelles)
        self.vitesse_actuelle = max(0, min(20, self.vitesse_actuelle))
        
        return round(self.vitesse_actuelle, 1)

class CapteurDebitEau:
    """Capteur de débit d'eau pour l'irrigation"""
    def __init__(self):
        self.eau_totale_utilisee = 0
        self.debit_max = 8.5
        
    def simuler(self, est_en_irrigation):
        if est_en_irrigation:
            # Débit variable avec petites fluctuations
            debit = self.debit_max * random.uniform(0.8, 1.0)
            # Ajouter au total (approximation: 1 cycle = 1 minute)
            self.eau_totale_utilisee += debit
        else:
            debit = 0
            
        return round(debit, 1), round(self.eau_totale_utilisee, 1)


class CapteurPH:
    """Capteur de pH du sol avec variations réalistes"""
    def __init__(self, ph_initial=6.5):
        self.ph_actuel = ph_initial  # pH neutre au départ
        
    def simuler(self, est_en_irrigation, pleut):
        """
        Simule les variations de pH du sol
        - L'irrigation peut légèrement alcaliniser (dépend de l'eau)
        - La pluie acidifie légèrement le sol
        - Variations naturelles minimes
        """
        # pH naturel reste stable autour de 6.0-7.5 pour la plupart des sols agricoles
        
        # Effet de la pluie (acidifie légèrement)
        if pleut:
            variation = random.uniform(-0.05, -0.01)
            self.ph_actuel += variation
        
        # Effet de l'irrigation (peut alcaliniser très légèrement selon l'eau)
        if est_en_irrigation:
            variation = random.uniform(-0.02, 0.03)
            self.ph_actuel += variation
        
        # Petite variation aléatoire naturelle
        bruit = random.uniform(-0.01, 0.01)
        self.ph_actuel += bruit
        
        # Stabilisation progressive vers pH neutre (buffering naturel du sol)
        ph_cible = 6.5
        self.ph_actuel = self.ph_actuel * 0.95 + ph_cible * 0.05
        
        # Limiter à des valeurs réalistes (5.5 - 7.5)
        self.ph_actuel = max(5.5, min(7.5, self.ph_actuel))
        
        return round(self.ph_actuel, 2)
