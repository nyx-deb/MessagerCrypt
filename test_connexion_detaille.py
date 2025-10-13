#!/usr/bin/env python3
"""
Test de connexion détaillé pour MessagerCrypt
"""

import socket
import sys
import json
import time
from pathlib import Path

# Ajout du répertoire parent au path pour les imports
sys.path.append(str(Path(__file__).parent))

def test_connection_step_by_step():
    """Test de connexion étape par étape"""
    print("🧪 TEST DE CONNEXION DÉTAILLÉ")
    print("=" * 40)
    
    # Demander l'IP du serveur
    server_ip = input("IP du serveur (Entrée pour 192.168.1.101): ").strip()
    if not server_ip:
        server_ip = "192.168.1.101"
    
    server_port = input("Port du serveur (Entrée pour 8888): ").strip()
    if not server_port:
        server_port = 8888
    else:
        try:
            server_port = int(server_port)
        except:
            server_port = 8888
    
    print(f"\n🔗 Test de connexion à {server_ip}:{server_port}")
    print("=" * 50)
    
    # Étape 1: Création du socket
    print("1. 📡 Création du socket...")
    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.settimeout(10)  # Timeout de 10 secondes
        print("   ✅ Socket créé avec succès")
    except Exception as e:
        print(f"   ❌ Erreur création socket: {e}")
        return False
    
    # Étape 2: Test de connexion
    print("2. 🔌 Tentative de connexion...")
    try:
        test_socket.connect((server_ip, server_port))
        print("   ✅ Connexion établie avec succès")
    except socket.timeout:
        print("   ❌ Timeout - Le serveur ne répond pas")
        test_socket.close()
        return False
    except ConnectionRefusedError:
        print("   ❌ Connexion refusée - Le serveur n'écoute pas sur ce port")
        test_socket.close()
        return False
    except Exception as e:
        print(f"   ❌ Erreur de connexion: {e}")
        test_socket.close()
        return False
    
    # Étape 3: Test d'envoi de données
    print("3. 📤 Test d'envoi de données...")
    try:
        test_message = {
            "type": "test_connection",
            "message": "Hello from test client",
            "timestamp": time.time()
        }
        
        message_json = json.dumps(test_message)
        test_socket.send(message_json.encode('utf-8'))
        print("   ✅ Données envoyées avec succès")
    except Exception as e:
        print(f"   ❌ Erreur envoi données: {e}")
        test_socket.close()
        return False
    
    # Étape 4: Test de réception
    print("4. 📥 Test de réception...")
    try:
        test_socket.settimeout(5)
        response = test_socket.recv(1024)
        if response:
            print(f"   ✅ Données reçues: {response.decode('utf-8')[:100]}...")
        else:
            print("   ⚠️  Aucune donnée reçue")
    except socket.timeout:
        print("   ⚠️  Timeout réception - Pas de réponse du serveur")
    except Exception as e:
        print(f"   ❌ Erreur réception: {e}")
    
    # Fermeture
    test_socket.close()
    print("5. 🔚 Connexion fermée")
    
    return True

def test_with_messagercrypt_client():
    """Test avec le client MessagerCrypt"""
    print("\n🔐 TEST AVEC CLIENT MESSAGERCRYPT")
    print("=" * 40)
    
    try:
        from src.client import MessagerCryptClient
        
        # Demander les paramètres
        server_ip = input("IP du serveur (Entrée pour 192.168.1.101): ").strip()
        if not server_ip:
            server_ip = "192.168.1.101"
        
        server_port = input("Port du serveur (Entrée pour 8888): ").strip()
        if not server_port:
            server_port = 8888
        else:
            try:
                server_port = int(server_port)
            except:
                server_port = 8888
        
        print(f"\n🔗 Test avec client MessagerCrypt vers {server_ip}:{server_port}")
        
        # Création du client
        client = MessagerCryptClient(host=server_ip, port=server_port)
        
        # Test de connexion
        print("1. 🔌 Tentative de connexion...")
        if client.connect():
            print("   ✅ Connexion réussie avec le client MessagerCrypt")
            
            # Test d'authentification (sans vraie authentification)
            print("2. 🔐 Test d'authentification...")
            # On ne peut pas tester l'auth sans vraies données, mais on peut voir si le serveur répond
            
            client.disconnect()
            print("3. 🔚 Déconnexion réussie")
            return True
        else:
            print("   ❌ Échec de connexion avec le client MessagerCrypt")
            return False
            
    except ImportError as e:
        print(f"❌ Erreur import client: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur test client: {e}")
        return False

def check_server_logs():
    """Vérifie les logs du serveur"""
    print("\n📋 VÉRIFICATION DES LOGS")
    print("=" * 30)
    
    log_file = Path("logs/server.log")
    if log_file.exists():
        print("✅ Fichier de log serveur trouvé")
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"📄 {len(lines)} lignes dans le log")
                
                # Afficher les dernières lignes
                print("\n🔍 Dernières lignes du log:")
                for line in lines[-10:]:
                    print(f"   {line.strip()}")
                    
        except Exception as e:
            print(f"❌ Erreur lecture log: {e}")
    else:
        print("❌ Fichier de log serveur non trouvé")
        print("   → Le serveur n'a peut-être pas été démarré")

def check_client_logs():
    """Vérifie les logs du client"""
    print("\n📋 VÉRIFICATION DES LOGS CLIENT")
    print("=" * 35)
    
    log_file = Path("logs/client.log")
    if log_file.exists():
        print("✅ Fichier de log client trouvé")
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"📄 {len(lines)} lignes dans le log")
                
                # Afficher les dernières lignes
                print("\n🔍 Dernières lignes du log:")
                for line in lines[-10:]:
                    print(f"   {line.strip()}")
                    
        except Exception as e:
            print(f"❌ Erreur lecture log: {e}")
    else:
        print("❌ Fichier de log client non trouvé")

def main():
    """Fonction principale"""
    print("🚀 TEST DE CONNEXION DÉTAILLÉ MESSAGERCRYPT")
    print("=" * 60)
    
    print("Choisissez un test :")
    print("1. 🧪 Test de connexion basique")
    print("2. 🔐 Test avec client MessagerCrypt")
    print("3. 📋 Vérifier les logs")
    print("4. 🔍 Test complet")
    
    choice = input("\nVotre choix (1-4): ").strip()
    
    if choice == "1":
        test_connection_step_by_step()
    elif choice == "2":
        test_with_messagercrypt_client()
    elif choice == "3":
        check_server_logs()
        check_client_logs()
    elif choice == "4":
        print("🔍 TEST COMPLET")
        print("=" * 20)
        test_connection_step_by_step()
        test_with_messagercrypt_client()
        check_server_logs()
        check_client_logs()
    else:
        print("❌ Choix invalide")
    
    print(f"\n💡 CONSEILS :")
    print("=" * 15)
    print("1. Assurez-vous que le serveur est démarré")
    print("2. Vérifiez que le firewall autorise le port 8888")
    print("3. Vérifiez que les deux PC sont sur le même réseau")
    print("4. Consultez les logs pour plus de détails")

if __name__ == "__main__":
    main()
