"""
Script de test pour vérifier les nouvelles fonctionnalités
"""
import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def test_historique():
    """Test de l'endpoint historique"""
    print("\n📊 TEST: Historique 24h")
    print("=" * 50)
    response = requests.get(f"{BASE_URL}/historique-24h")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Historique récupéré: {data['total_points']} points")
        print(f"   Période: {data['periode']}")
        if data['total_points'] > 0:
            dernier = data['data'][-1]
            print(f"   Dernier point: Temp={dernier['temperature']}°C, Hum={dernier['humidity']}%")
    else:
        print(f"❌ Erreur: {response.status_code}")

def test_configuration():
    """Test de la configuration dynamique"""
    print("\n⚙️ TEST: Configuration Dynamique")
    print("=" * 50)
    
    # Récupérer la config actuelle
    response = requests.get(f"{BASE_URL}/configuration")
    if response.status_code == 200:
        config = response.json()
        print(f"✅ Configuration actuelle:")
        print(f"   Type plante: {config['type_plante']}")
        print(f"   Saison: {config['saison']}")
        print(f"   Mode: {config['mode']}")
        print(f"   Seuils: {config['seuil_declenchement']}% → {config['seuil_arret']}%")
        
        # Modifier la configuration
        print("\n🔧 Modification de la configuration...")
        nouvelle_config = {
            "type_plante": "mais",
            "saison": "printemps",
            "mode": "intensif"
        }
        
        response = requests.post(f"{BASE_URL}/configuration", json=nouvelle_config)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {result['message']}")
            print(f"   Nouvelle config: {result['config']['type_plante']} / {result['config']['saison']} / {result['config']['mode']}")
        else:
            print(f"❌ Erreur: {response.status_code}")
    else:
        print(f"❌ Erreur: {response.status_code}")

def test_alertes():
    """Test du système d'alertes"""
    print("\n⚠️ TEST: Système d'Alertes et Logs")
    print("=" * 50)
    
    response = requests.get(f"{BASE_URL}/alertes-logs?limit=5")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Logs récupérés: {data['total']} événements au total")
        print(f"   Affichage des 5 derniers:")
        for log in data['logs']:
            print(f"   - [{log['type']}] {log['message']}")
    else:
        print(f"❌ Erreur: {response.status_code}")

def main():
    print("\n" + "=" * 50)
    print("🧪 TEST DES NOUVELLES FONCTIONNALITÉS")
    print("=" * 50)
    
    try:
        test_historique()
        time.sleep(1)
        
        test_configuration()
        time.sleep(1)
        
        test_alertes()
        
        print("\n" + "=" * 50)
        print("✅ TESTS TERMINÉS")
        print("=" * 50)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERREUR: Backend non accessible!")
        print("💡 Démarrez le backend: cd backend && uvicorn main:app --reload")
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")

if __name__ == "__main__":
    main()
