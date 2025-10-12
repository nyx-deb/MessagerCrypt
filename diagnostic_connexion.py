#!/usr/bin/env python3
"""
Script de diagnostic pour les problèmes de connexion MessagerCrypt
"""

import socket
import sys
import subprocess
import time
from pathlib import Path

# Ajout du répertoire parent au path pour les imports
sys.path.append(str(Path(__file__).parent))

def get_local_ip():
    """Récupère l'adresse IP locale"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        print(f"❌ Erreur lors de la récupération de l'IP locale: {e}")
        return None

def test_port_connection(host, port):
    """Test de connexion à un port spécifique"""
    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.settimeout(5)
        result = test_socket.connect_ex((host, port))
        test_socket.close()
        
        if result == 0:
            print(f"✅ Port {port} ouvert sur {host}")
            return True
        else:
            print(f"❌ Port {port} fermé sur {host}")
            return False
    except Exception as e:
        print(f"❌ Erreur test port {host}:{port}: {e}")
        return False

def check_server_status():
    """Vérifie si le serveur est en cours d'exécution"""
    print("🔍 VÉRIFICATION DU SERVEUR")
    print("=" * 30)
    
    # Test localhost
    localhost_ok = test_port_connection("127.0.0.1", 8888)
    
    # Test IP locale
    local_ip = get_local_ip()
    if local_ip:
        print(f"🌐 IP locale détectée: {local_ip}")
        local_ip_ok = test_port_connection(local_ip, 8888)
    else:
        local_ip_ok = False
    
    return localhost_ok or local_ip_ok

def check_firewall():
    """Vérifie les règles du firewall"""
    print("\n🔥 VÉRIFICATION DU FIREWALL")
    print("=" * 30)
    
    try:
        if sys.platform == "win32":
            result = subprocess.run([
                "netsh", "advfirewall", "firewall", "show", "rule", "name=MessagerCrypt"
            ], capture_output=True, text=True, timeout=10)
            
            if "MessagerCrypt" in result.stdout:
                print("✅ Règles firewall MessagerCrypt trouvées")
                return True
            else:
                print("❌ Aucune règle firewall MessagerCrypt")
                return False
        else:
            print("ℹ️  Vérification firewall non supportée sur cette plateforme")
            return True
    except Exception as e:
        print(f"❌ Erreur vérification firewall: {e}")
        return False

def test_network_connectivity():
    """Test la connectivité réseau"""
    print("\n🌐 TEST DE CONNECTIVITÉ RÉSEAU")
    print("=" * 35)
    
    # Test ping vers Google DNS
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ["ping", "-n", "1", "8.8.8.8"],
                capture_output=True, text=True, timeout=10
            )
        else:
            result = subprocess.run(
                ["ping", "-c", "1", "8.8.8.8"],
                capture_output=True, text=True, timeout=10
            )
        
        if result.returncode == 0:
            print("✅ Connectivité Internet: OK")
            return True
        else:
            print("⚠️  Connectivité Internet: Problème détecté")
            return False
    except Exception as e:
        print(f"⚠️  Test de connectivité Internet: {e}")
        return False

def check_processes():
    """Vérifie les processus en cours"""
    print("\n🔍 VÉRIFICATION DES PROCESSUS")
    print("=" * 35)
    
    try:
        if sys.platform == "win32":
            result = subprocess.run([
                "tasklist", "/FI", "IMAGENAME eq python.exe"
            ], capture_output=True, text=True, timeout=10)
            
            if "python.exe" in result.stdout:
                print("✅ Processus Python détectés")
                print("Processus Python en cours:")
                for line in result.stdout.split('\n'):
                    if "python.exe" in line:
                        print(f"  {line.strip()}")
                return True
            else:
                print("❌ Aucun processus Python détecté")
                return False
        else:
            result = subprocess.run([
                "ps", "aux"
            ], capture_output=True, text=True, timeout=10)
            
            python_processes = [line for line in result.stdout.split('\n') if 'python' in line]
            if python_processes:
                print("✅ Processus Python détectés")
                for process in python_processes[:3]:  # Afficher les 3 premiers
                    print(f"  {process.strip()}")
                return True
            else:
                print("❌ Aucun processus Python détecté")
                return False
    except Exception as e:
        print(f"❌ Erreur vérification processus: {e}")
        return False

def show_troubleshooting_steps():
    """Affiche les étapes de dépannage"""
    print("\n🔧 ÉTAPES DE DÉPANNAGE")
    print("=" * 25)
    
    print("1. 🖥️  VÉRIFIER LE SERVEUR :")
    print("   - Le serveur est-il démarré ?")
    print("   - Y a-t-il des erreurs dans les logs ?")
    print("   - Le port 8888 est-il libre ?")
    print()
    
    print("2. 🔥 CONFIGURER LE FIREWALL :")
    print("   - Exécuter: python configure_firewall.py (en tant qu'administrateur)")
    print("   - Ou configurer manuellement le port 8888")
    print()
    
    print("3. 🌐 VÉRIFIER LE RÉSEAU :")
    print("   - Les deux PC sont-ils sur le même réseau ?")
    print("   - Tester avec: ping IP_DU_SERVEUR")
    print("   - Tester avec: telnet IP_DU_SERVEUR 8888")
    print()
    
    print("4. 🔍 VÉRIFIER LES LOGS :")
    print("   - Consulter logs/server.log")
    print("   - Consulter logs/client.log")
    print()
    
    print("5. 🧪 TEST SIMPLE :")
    print("   - Démarrer le serveur sur un PC")
    print("   - Tester la connexion depuis le même PC d'abord")
    print("   - Puis tester depuis l'autre PC")

def main():
    """Fonction principale de diagnostic"""
    print("🚀 DIAGNOSTIC DE CONNEXION MESSAGERCRYPT")
    print("=" * 60)
    
    # Tests de diagnostic
    server_ok = check_server_status()
    firewall_ok = check_firewall()
    network_ok = test_network_connectivity()
    processes_ok = check_processes()
    
    # Résumé
    print("\n📊 RÉSUMÉ DU DIAGNOSTIC")
    print("=" * 30)
    
    results = [
        ("Serveur", server_ok),
        ("Firewall", firewall_ok),
        ("Réseau", network_ok),
        ("Processus", processes_ok)
    ]
    
    for test_name, result in results:
        status = "✅ OK" if result else "❌ PROBLÈME"
        print(f"{test_name}: {status}")
    
    # Recommandations
    if not server_ok:
        print("\n⚠️  PROBLÈME PRINCIPAL: Serveur non accessible")
        print("   → Démarrer le serveur avec: python src/main.py")
        print("   → Choisir 'Démarrer le serveur'")
    
    if not firewall_ok:
        print("\n⚠️  PROBLÈME: Firewall non configuré")
        print("   → Exécuter: python configure_firewall.py (en tant qu'administrateur)")
    
    if not network_ok:
        print("\n⚠️  PROBLÈME: Connectivité réseau")
        print("   → Vérifier la connexion Internet")
        print("   → Vérifier que les PC sont sur le même réseau")
    
    # Étapes de dépannage
    show_troubleshooting_steps()
    
    print(f"\n💡 PROCHAINES ÉTAPES :")
    print("=" * 20)
    print("1. Corriger les problèmes identifiés ci-dessus")
    print("2. Redémarrer le serveur")
    print("3. Tester la connexion")
    print("4. Consulter les logs en cas d'erreur")

if __name__ == "__main__":
    main()
